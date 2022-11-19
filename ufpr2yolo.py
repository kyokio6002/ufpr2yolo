'''convert AOSP to YOLO'''
from pathlib import Path
import random
import shutil

from pprint import pprint

import cv2
from PIL import Image, ImageDraw


BASE_DIR = Path(__file__).resolve().parent
TRAIN_PATH = BASE_DIR.joinpath('training')
TEST_PATH = BASE_DIR.joinpath('testing')
VALID_PATH = BASE_DIR.joinpath('validation')

OUTPUT_TRAIN_PATH = BASE_DIR.joinpath('train')
OUTPUT_TRAIN_PATH = BASE_DIR.joinpath('test')
OUTPUT_TEST_PATH = BASE_DIR.joinpath('valid')


def get_text_path(image_path, dir_path):
    '''xxx/file.png to xxx/file.txt'''
    image_name = Path(image_path.name)
    text_path = dir_path.joinpath(image_name.stem + '.txt')
    return text_path


def make_output_dir():
    # TODO
    if not OUTPUT_TRAIN_PATH.exists():
        OUTPUT_TRAIN_PATH.mkdir()
    if not OUTPUT_TEST_PATH.exists():
        OUTPUT_TEST_PATH.mkdir()


def show_rectangle(image_path, left, upper, right, bottom):
    # TODO
    if image_path.name == '1.jpg':
        print(f'upper:{upper}')
        print(f'bottom:{bottom}')
        print(f'right:{right}')
        print(f'left:{left}')

        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            (left, upper, right, bottom),
            outline=(255, 0, 0),
            width=5
        )
        image.show()


def convert_location(left, upper, right, bottom, input_image_path):
    # TODO
    (h, w, _) = cv2.imread(str(input_image_path)).shape
    x_center = float((right + left) / 2) / w
    y_center = float((upper + bottom) / 2) / h
    width = float(right - left) / w
    height = float(bottom - upper) / h
    return x_center, y_center, width, height


def remove_tab_and_newline(str_line):
    '''key, value(list)'''
    str_list = str_line.split(':')
    key = str_list[0].strip('\t')
    value = str_list[1].strip('\n').split()
    return key, value


def return_dict_from_ufpr_format(lines):
    plate_dict = {}
    for line in lines:
        key, value_list = remove_tab_and_newline(line)
        if 'char' in key or 'plate' in key:
            plate_dict[key] = value_list
    return plate_dict


def update_dict_key(plate_dict):
    plate_chars = plate_dict['plate']
    index = 1
    for char in plate_chars[0]:
        if char == '-':
            continue
        key_before = f'char {str(index)}'
        plate_dict[char] = plate_dict[key_before]
        del plate_dict[key_before]
        index += 1
    return plate_dict


def convert2yolo(input_image_path, input_text_path,input_path, debag=False):
    '''???'''
    with open(input_text_path, mode='r', encoding='utf_8') as f:
        lines = f.readlines()
        return_dict = return_dict_from_ufpr_format(lines)
        if debag:
            pprint(return_dict)
        plate_dict = update_dict_key(return_dict)
        if debag:
            pprint(plate_dict)

        # TODO
        # 続き


        # show_rectangle(input_image_path, left, upper, right, bottom)

        # 書き込み
        # output_path = OUTPUT_TRAIN_PATH if train_or_test == 'train' else OUTPUT_TEST_PATH
        # output_text_path = output_path.joinpath(f'{set_type}{input_text_path.name}')
        # output_image_path = output_path.joinpath(f'{set_type}{input_image_path.name}')
        # print(f'output_path:{output_path}')
        # print(f'output_text_path:{output_text_path}')
        # with open(output_text_path, mode='w', encoding='utf_8') as f:
        #     x_center, y_center, width, height = convert_location(left, upper, right, bottom, input_image_path)
        #     f.write(f'0 {x_center:06f} {y_center:06f} {width:06f} {height:06f}\n')
        # shutil.copy(input_image_path, output_image_path)


def main(ext='png'):

    data = {
        'train': TRAIN_PATH,
        'test' : TEST_PATH,
        'valid': VALID_PATH
    }
    count = 0
    for key, path in data.items():
        track_dir_paths = path.glob('track*')
        for track_dir_path in track_dir_paths:
            image_paths = track_dir_path.glob(f'*.{ext}')
            for image_path in image_paths:
                text_path = get_text_path(image_path, track_dir_path)
                convert2yolo(image_path, text_path, path, debag=True)
                count += 1
                # print('\r', f'count:{count}', end='')


def split_data():
    base_dir = Path(__file__).resolve().parent
    input_train_path = base_dir.joinpath('train')
    input_test_path = base_dir.joinpath('test')

    train_rate = 0.8
    train_valid_images = list(input_train_path.glob('*.jpg'))

    random.seed(100)
    random.shuffle(train_valid_images)

    train_images = train_valid_images[:int(len(train_valid_images)*train_rate)]
    valid_images = train_valid_images[int(len(train_valid_images)*train_rate):]
    test_images = list(input_test_path.glob('*.jpg'))

    datas = {
        'train': train_images,
        'valid': valid_images,
        'test': test_images
    }

    for key, value in datas.items():
        text_path = base_dir.joinpath(f'cfg/{key}.txt')
        print(f'{key}:{len(value)}')
        with open(text_path, mode='w', encoding='utf_8') as f:
            for image in value:
                f.write(str(image)+'\n')


if __name__ == '__main__':
    # make_output_dir()
    main()
    # split_data()
