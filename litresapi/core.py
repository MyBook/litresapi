import datetime
import hashlib
import io
import logging
import re
import time

import lxml
import requests
from requests.adapters import HTTPAdapter, Retry
from requests.compat import urljoin

from litresapi.exceptions import LitresAPIException
from . import xmltodict

logger = logging.getLogger(__name__)


class LitresApi(object):
    """
    Litres API wrapper

    Docs: https://docs.litres.ru/x/goh8
    """
    force_list = (
        'author',
        'genre',
        'sequence',
        'copyright',
    )

    def __init__(self, partner_id=None, secret_key=None, xml=False):
        # Строковой ID партнера. Обычно представлен четырьмя символами.
        # Используется при запросе обновлений (см. 1.1).
        # Также используется при скачивании файла партнером типа «магазин на стороне партнера» (см. 2.1).
        # Выдается партнеру тех. службой «ЛитРес» при заключении договора.
        self.partner_id = partner_id

        # Секретный ключ, используемый для MD5-подписи и требуемый при авторизации запросов
        # от партнера к ЛитРес (см. 2.1, 3.1, 4.1, 4.3), а также от ЛитРес к партнерам (см. 3.1).
        # Выдается партнеру тех. службой «ЛитРес» при заключении договора.
        self.secret_key = secret_key

        self.base_url = 'https://{domain_prefix}.litres.ru/'

        # Retry request on network errors and 500 response
        self.session = requests.session()
        self.session.mount('https://', HTTPAdapter(max_retries=Retry(total=3, status_forcelist=[500])))

        self.response_as_dict = not xml

    def _request(self, resource, method='GET', **kwargs):
        domain_prefix = kwargs.pop('domain_prefix', 'sp')
        url = urljoin(self.base_url.format(domain_prefix=domain_prefix), resource)
        response = None
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
        except (requests.HTTPError, requests.exceptions.RetryError):
            raise LitresAPIException('failed to open', response=response)
        except (requests.exceptions.ConnectionError, IOError):
            raise LitresAPIException('connection error', response=response)
        else:
            return response

    def _get_freshbook_sha(self, checkpoint):
        timestamp = str(int(time.time()))
        signature = ':'.join([timestamp, self.secret_key, checkpoint])
        return {
            'sha': hashlib.sha256(signature.encode('utf-8')).hexdigest(),
            'timestamp': timestamp
        }

    def get_fresh_book(self, start_date=None, end_date=None, uuid=None, book_type='EBOOK', moreplaces=None, **kwargs):
        BOOK_TYPES = {
            'EBOOK': '0',
            'AUDIO': '1',
            'PDF': '4',
            'ADOBEDRM': '11',
            'ALL': 'all'
        }
        if uuid:
            start_date = datetime.datetime(2010, 5, 16)

        params = {
            'checkpoint': str(start_date.replace(microsecond=0)),
            'endpoint': str(end_date.replace(microsecond=0)) if end_date else None,
            'uuid': uuid,
            'type': BOOK_TYPES.get(book_type, book_type),
            'moreplaces': moreplaces,
            'place': self.partner_id
        }
        params = {k: v for k, v in params.items() if v is not None}
        params.update(self._get_freshbook_sha(params['checkpoint']))
        response = self._request('get_fresh_book/', params=params, **kwargs)
        return self.parse_fresh_book(response.content)

    def parse_fresh_book(self, content):
        content = (content
                   .replace(b'<![CDATA[', b'')
                   .replace(b']]>', b'')
                   .replace(b'<annotation>', b'<annotation><![CDATA[')
                   .replace(b'</annotation>', b']]></annotation>'))
        if not self.response_as_dict:
            xml_iterator = lxml.etree.iterparse(
                io.BytesIO(content),
                events=('end',),
                huge_tree=True,
                tag=['updated-book', 'fb-updates', 'removed-book'],
            )
            for _, element in xml_iterator:
                if element.tag == 'updated-book':
                    yield element
                    element.clear()
                    while element.getprevious() is not None:
                        del element.getparent()[0]
        else:
            for path, item in xmltodict.parse(content, generator=True, item_depth=2,
                                              force_list=self.force_list):
                tag_name, book_meta = path[-1]
                if tag_name == 'removed-book':
                    book = book_meta
                elif tag_name == 'updated-book':
                    book = item
                    for k, v in book_meta.items():
                        book['@%s' % k] = v
                book['@tag'] = tag_name
                yield book

    def _get_the_book_hash(self, external_id):
        signature = ':'.join([external_id, self.secret_key])
        return {
            'md5': hashlib.md5(signature.encode('utf-8')).hexdigest(),
        }

    def get_the_book(self, external_id, file_type=None, file_id=None, **kwargs):
        """

        :param external_id:
        :param file_type:
        :param file_id:
        :param kwargs:
        :return:
        """
        params = {
            'book': external_id.lower(),
            'type': file_type,
            'file': file_id,
            'place': self.partner_id
        }
        params = {k: v for k, v in params.items() if v is not None}
        params.update(self._get_the_book_hash(external_id.lower()))
        response = self._request('get_the_book/', params=params, **kwargs)
        self.check_response(response)

        return response

    def save_the_book(self, *args, **kwargs):
        """ Save single bookfile
        :param args:
        :param kwargs:
        :return:
        """
        kwargs['stream'] = True
        response = self.get_the_book(*args, **kwargs)
        filename = re.findall('filename="(\S+)"', response.headers['Content-Disposition'])[0]
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if not chunk:
                    continue
                f.write(chunk)
                f.flush()
        return filename

    def get_cover(self, book_id=None, file_ext='jpg', book=None, **kwargs):
        if book:
            book_id = book['@id']
            file_ext = book['@cover']
            if not file_ext:
                return None
        # we are taking max size cover
        cover_dir = '/pub/c/cover_max1500/{}.jpg'.format(book_id)
        response = self._request(cover_dir, domain_prefix='partnersdnld', **kwargs)
        self.check_response(response)

        return response

    def get_genres(self, **kwargs):
        response = self._request('genres_list_2/', **kwargs)
        if self.response_as_dict:
            return xmltodict.parse(response.content)['genres']['genre']
        else:
            return lxml.etree.fromstring(response.content)

    def check_response(self, response):
        content_type = response.headers.get('content-type', '').lower().strip()
        if not content_type:
            raise LitresAPIException('No content type response', response=response)
        if re.search('text/xml', content_type):
            raise LitresAPIException('Got xml instead of file', response=response)
