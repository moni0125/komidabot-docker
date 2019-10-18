import datetime, enum, pdf2image, re, requests, tempfile
import dateutil.parser as date_parser
from collections import namedtuple
from lxml import html
from pdfquery import PDFQuery
from PIL import ImageDraw
from PIL.Image import Image
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from komidabot.models import Campus


class FrameFoodType(enum.Enum):
    SOUP = 1
    MEAT = 2
    VEGAN = 3
    GRILL = 4
    PASTA = 5


class FrameDay(enum.Enum):
    WEEKLY = -1
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5


# Boxes are expressed in a percentage of the page size, the origin is the top-left corner
Box = namedtuple('Box', ['x', 'y', 'width', 'height'])
Frame = namedtuple('Frame', ['day', 'box', 'items'])
FrameItem = namedtuple('FrameItem', ['food_type', 'is_price', 'box'])
ParseResult = namedtuple('ParseResult', ['day', 'food_type', 'name', 'price'])

DATE_LOCATION = Box(0.703, 0.083, 0.280, 0.022)

BOX_SOUP_LEFT = [
    FrameItem(FrameFoodType.SOUP, False, Box(0.190, 0.010, 0.590, 0.240)),
    FrameItem(FrameFoodType.SOUP, True, Box(0.770, 0.010, 0.220, 0.240))
]
BOX_SOUP_RIGHT = [
    FrameItem(FrameFoodType.SOUP, False, Box(0.190, 0.010, 0.540, 0.240)),
    FrameItem(FrameFoodType.SOUP, True, Box(0.720, 0.010, 0.220, 0.240))
]
BOX_VEGAN_LEFT = [
    FrameItem(FrameFoodType.VEGAN, False, Box(0.190, 0.250, 0.590, 0.410)),
    FrameItem(FrameFoodType.VEGAN, True, Box(0.770, 0.250, 0.220, 0.410))
]
BOX_VEGAN_RIGHT = [
    FrameItem(FrameFoodType.VEGAN, False, Box(0.190, 0.250, 0.540, 0.410)),
    FrameItem(FrameFoodType.VEGAN, True, Box(0.720, 0.250, 0.220, 0.410))
]
BOX_MEAT_LEFT = [
    FrameItem(FrameFoodType.MEAT, False, Box(0.190, 0.660, 0.590, 0.325)),
    FrameItem(FrameFoodType.MEAT, True, Box(0.770, 0.660, 0.220, 0.325))
]
BOX_MEAT_RIGHT = [
    FrameItem(FrameFoodType.MEAT, False, Box(0.190, 0.660, 0.540, 0.325)),
    FrameItem(FrameFoodType.MEAT, True, Box(0.720, 0.660, 0.220, 0.325))
]
BOX_GRILL = [
    FrameItem(FrameFoodType.GRILL, False, Box(0.190, 0.250, 0.540, 0.410)),
    FrameItem(FrameFoodType.GRILL, True, Box(0.720, 0.250, 0.220, 0.410))
]
BOX_PASTA = [
    FrameItem(FrameFoodType.PASTA, False, Box(0.190, 0.660, 0.540, 0.340)),
    FrameItem(FrameFoodType.PASTA, True, Box(0.720, 0.660, 0.220, 0.340))
]

FRAMES = [
    Frame(FrameDay.MONDAY, Box(0.076, 0.177, 0.406, 0.197), (
        tuple(BOX_SOUP_LEFT + BOX_VEGAN_LEFT + BOX_MEAT_LEFT)
    )),
    Frame(FrameDay.TUESDAY, Box(0.515, 0.177, 0.406, 0.197), (
        tuple(BOX_SOUP_RIGHT + BOX_VEGAN_RIGHT + BOX_MEAT_RIGHT)
    )),
    Frame(FrameDay.WEDNESDAY, Box(0.076, 0.429, 0.406, 0.197), (
        tuple(BOX_SOUP_LEFT + BOX_VEGAN_LEFT + BOX_MEAT_LEFT)
    )),
    Frame(FrameDay.THURSDAY, Box(0.515, 0.429, 0.406, 0.197), (
        tuple(BOX_SOUP_RIGHT + BOX_VEGAN_RIGHT + BOX_MEAT_RIGHT)
    )),
    Frame(FrameDay.FRIDAY, Box(0.076, 0.683, 0.406, 0.197), (
        tuple(BOX_SOUP_LEFT + BOX_VEGAN_LEFT + BOX_MEAT_LEFT)
    )),
    Frame(FrameDay.WEEKLY, Box(0.515, 0.683, 0.406, 0.197), (
        tuple(BOX_GRILL + BOX_PASTA)
    ))
]


class ParsedDocument:
    def __init__(self, start_date: datetime.date, end_date: datetime.date, frames: Dict[FrameDay, Image]):
        self.start_date = start_date
        self.end_date = end_date
        self.parse_results = []  # type:  List[ParseResult]
        self.frames = frames

    def add_parse_result(self, result: ParseResult):
        self.parse_results.append(result)


class MenuScraper:
    def __init__(self, campus: Campus):
        self.page_url = campus.page_url
        self.campus_short_name = campus.short_name
        self.pdf_location = None
        self.file = None
        self.pdf_q = None
        self.pdf_width = 0
        self.pdf_height = 0
        self.image_width = 0
        self.image_height = 0
        self.parse_result = None
        self.full_frame = None  # type: Optional[Image]
        self.frames = dict()  # type: Dict[FrameDay, Image]

    def find_pdf_location(self):
        if self.pdf_location is not None:
            return self.pdf_location

        page_response = requests.get(self.page_url)

        if page_response.status_code != 200:
            pass  # TODO: What if this fails?

        tree = html.fromstring(page_response.content)

        matches = [str(elm) for elm in tree.xpath("//a[contains(@href, '.pdf')][contains(@href, '{}')]/@href".
                                                  format(self.campus_short_name.upper())) if elm.endswith('.pdf')]
        matches = list(set(matches))

        print(matches, flush=True)

        if len(matches) < 1:
            return None  # TODO: Needs better resolution
        elif len(matches) > 1:
            pass  # TODO: Needs better resolution

        page_url = urlparse(page_response.url)
        pdf_url = urlparse(matches[0])

        print(page_url)
        print(pdf_url)

        self.pdf_location = '{scheme}://{netloc}{path}'.format(scheme=pdf_url.scheme or page_url.scheme,
                                                               netloc=pdf_url.netloc or page_url.netloc,
                                                               path=pdf_url.path)

        return self.pdf_location

    def download_pdf(self):
        if self.pdf_location is None:
            raise RuntimeError('PDF location missing')

        response = requests.get(self.pdf_location)

        response.raise_for_status()

        self.file = tempfile.NamedTemporaryFile()
        self.file.write(response.content)
        self.file.seek(0)

        self.pdf_q = PDFQuery(self.file)  # Origin is bottom left
        self.pdf_q.load()

        layout = self.pdf_q.get_layout(self.pdf_q.get_page(0))

        self.pdf_width = layout.width
        self.pdf_height = layout.height

        return self.file

    def parse_pdf(self):
        dates = re.split(' *- *', self.get_frame_text_safe(DATE_LOCATION))

        start_date = date_parser.parse(dates[0], date_parser.parserinfo(True)).date()
        end_date = date_parser.parse(dates[1], date_parser.parserinfo(True)).date()
        self.parse_result = ParsedDocument(start_date, end_date, self.frames)

        print('Start date: {}'.format(start_date))
        print('End date: {}'.format(end_date))

        data = dict()  # type: Dict[Tuple[FrameDay, FrameFoodType], Tuple[str, str]]

        for day, box, items in FRAMES:
            for food_type, is_price, sub_box in items:
                text = self.get_frame_text_safe(get_sub_frame(box, sub_box))

                pair = (day, food_type)

                if is_price:
                    data[pair] = (data[pair][0] if pair in data else None, text)
                else:
                    data[pair] = (text, data[pair][1] if pair in data else None)

                # print('Text for {}/{} ({}): {}'.format(day.name, food_type.name, 'price' if is_price else 'food',
                #                                        text))

            # print('Text for {}: {}'.format(day.name, self.get_frame_text_safe(box)))

        for (day, food_type), (name, price) in data.items():
            self.parse_result.add_parse_result(ParseResult(day, food_type, name, price))

        # print(pdf_q.tree.xpath('//LTTextBoxHorizontal'))
        #
        # for box in pdf_q.tree.xpath('//LTTextBoxHorizontal'):
        #     (x0, y0, x1, y1) = box.layout.bbox
        #     bboxes.append(box.layout.bbox)
        #     # text = pdf_q.pq('LTTextLineHorizontal:in_bbox("{},{},{},{}")'
        #     # .format(x0 - 1, y0 - 1, x1 + 1, y1 + 1)).text()
        #     text = pdf_q.pq('LTTextLineHorizontal:in_bbox("{},{},{},{}")'
        #                     .format(floor(x0), floor(y0), ceil(x1), ceil(y1))).text()
        #     print(text)

        return self.parse_result

    def generate_pictures(self):
        # TODO: Create smaller frames
        pages = pdf2image.convert_from_path(self.file.name)

        if len(pages) != 1:
            return  # TODO: Handle this special case

        self.full_frame = pages[0]

        for day, box, items in FRAMES:
            draw_square(self.full_frame, box, color='#00ff00')

            for food_type, is_price, sub_box in items:
                draw_square(self.full_frame, get_sub_frame(box, sub_box), color='#ff0000')

            self.frames[day] = crop_image(self.full_frame, box)

        draw_square(self.full_frame, DATE_LOCATION, color='#00ff00')

        # page.save('out.png', 'PNG')

        # frame_mon = crop_image(page, FRAME_LOCATIONS[0])
        # frame_tue = crop_image(page, FRAME_LOCATIONS[1])
        # frame_wed = crop_image(page, FRAME_LOCATIONS[2])
        # frame_thu = crop_image(page, FRAME_LOCATIONS[3])
        # frame_fri = crop_image(page, FRAME_LOCATIONS[4])
        # frame_wek = crop_image(page, FRAME_LOCATIONS[5])

        # frame_mon.show()
        # frame_tue.show()
        # frame_wed.show()
        # frame_thu.show()
        # frame_fri.show()
        # frame_wek.show()

    def get_frame_text_safe(self, frame):
        (x0, y0, width, height) = frame

        x0 *= self.pdf_width
        x1 = x0 + width * self.pdf_width
        y0 *= self.pdf_height
        y1 = y0 + height * self.pdf_height

        y0, y1 = y1, y0

        return self.get_box_text_safe((x0, self.pdf_height - y0, x1, self.pdf_height - y1))

    def get_box_text_safe(self, box):
        (x0, y0, x1, y1) = box

        return self.pdf_q.pq('LTTextLineHorizontal:in_bbox("{},{},{},{}")'
                             .format(x0 - 1, y0 - 1, x1 + 1, y1 + 1)).text().strip()


def get_sub_frame(frame, child):
    width = frame[2]
    height = frame[3]

    return (frame[0] + child[0] * width), (frame[1] + child[1] * height), \
           (child[2] * width), (child[3] * height)


def draw_square(image: Image, frame, color='#ff0000'):
    draw = ImageDraw.Draw(image)  # Origin is top left

    x0 = frame[0] * image.size[0]
    x1 = x0 + frame[2] * image.size[0]
    y0 = frame[1] * image.size[1]
    y1 = y0 + frame[3] * image.size[1]
    draw.rectangle((x0, y0, x1, y1), outline=color)


def crop_image(image: Image, frame):
    x0 = frame[0] * image.size[0]
    x1 = x0 + frame[2] * image.size[0]
    y0 = frame[1] * image.size[1]
    y1 = y0 + frame[3] * image.size[1]
    return image.crop((x0, y0, x1, y1))


def parse_price(price: str):
    split = re.split(' *[-/] *', price)
    if len(split) != 2:
        return None
    return [''.join(item.split(' ')) for item in split]
