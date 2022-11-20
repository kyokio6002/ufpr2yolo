'''convert AOSP to YOLO'''
from pathlib import Path
import random
import shutil

from pprint import pprint

import cv2
from PIL import Image, ImageDraw


BASE_DIR = Path(__file__).resolve().parent

TRAIN_PATH = BASE_DIR.joinpath('training')
VALID_PATH = BASE_DIR.joinpath('validation')
TEST_PATH = BASE_DIR.joinpath('testing')

OUTPUT_TRAIN_PATH = BASE_DIR.joinpath('train')
OUTPUT_VALID_PATH = BASE_DIR.joinpath('valid')
OUTPUT_TEST_PATH = BASE_DIR.joinpath('test')

CFG_PATH = BASE_DIR.joinpath('cfg')


def make_output_dir():

    if not CFG_PATH.exists():
        CFG_PATH.mkdir()

    if not OUTPUT_TRAIN_PATH.exists():
        OUTPUT_TRAIN_PATH.mkdir()
    if not OUTPUT_VALID_PATH.exists():
        OUTPUT_VALID_PATH.mkdir()
    if not OUTPUT_TEST_PATH.exists():
        OUTPUT_TEST_PATH.mkdir()


def get_text_path(image_path, dir_path):
    '''xxx/file.png to xxx/file.txt'''
    image_name = Path(image_path.name)
    text_path = dir_path.joinpath(image_name.stem + '.txt')
    return text_path


def remove_tab_and_newline(str_line):
    '''key, value(list)'''
    str_list = str_line.split(':')
    key = str_list[0].strip('\t')
    value_list = str_list[1].strip('\n').split()
    return key, value_list


def return_list_from_ufpr_format(lines):
    '''
    input: 'key: value'\n'key:value'...
    output: plate, plate_list
    '''
    plate = 'unknown'
    plate_list = []  # [plate [char, x, y, w, h]]
    for line in lines:
        key, value_list = remove_tab_and_newline(line)
        if 'char' in key or key == 'position_plate':
            plate_list.append([key, value_list])
        elif key == 'plate':
            plate = value_list[0]
    return plate, plate_list


def update_list_key(plate_chars, plate_list):
    index = 1
    update_plate_list = [['plate', plate_list[i][1]] for i in range(len(plate_list)) if plate_list[i][0] == 'position_plate']
    for char in plate_chars:
        if char == '-':
            continue
        update_plate_list.append([char, plate_list[index-1][1]])
        index += 1
    return update_plate_list


def show_rectangle(image_path, left, upper, right, bottom):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (left, upper, right, bottom),
        outline=(255, 0, 0),
        width=5
    )
    image.show()


def get_location(position_list):
    left = int(position_list[0])
    upper = int(position_list[1])
    right = int(position_list[0]) + int(position_list[2])
    bottom = int(position_list[1]) + int(position_list[3])
    return left, upper, right, bottom


def convert_location(input_image_path, left, upper, right, bottom):
    (h, w, _) = cv2.imread(str(input_image_path)).shape
    x_center = float((right + left) / 2) / w
    y_center = float((upper + bottom) / 2) / h
    width = float(right - left) / w
    height = float(bottom - upper) / h
    return x_center, y_center, width, height


def convert2yolo(input_image_path, input_text_path, input_path, output_path, class_name_dict, debag=False):
    '''???'''
    with open(input_text_path, mode='r', encoding='utf_8') as f:
        lines = f.readlines()
        plate, plate_list = return_list_from_ufpr_format(lines)
        if debag:
            print(f'plate: {plate}')
            pprint(plate_list)
        plate_list = update_list_key(plate, plate_list)
        if debag:
            pprint(plate_list)

        for char_set in plate_list:
            class_name = char_set[0]
            position_list = char_set[1]
            left, upper, right, bottom = get_location(position_list)
            # show_rectangle(input_image_path, left, upper, right, bottom)  # debug

            if class_name not in class_name_dict:
                class_name_dict[class_name] = len(class_name_dict)
            class_index = class_name_dict[class_name]

            output_image_path = output_path.joinpath(input_image_path.name)
            output_text_path = output_path.joinpath(input_text_path.name)
            with open(output_text_path, mode='a', encoding='utf_8') as f:
                # return rate: 0.0-1.0
                x_center, y_center, width, height = convert_location(input_image_path, left, upper, right, bottom)
                if debag:
                    print(f'{class_index} {x_center:06f} {y_center:06f} {width:06f} {height:06f}')
                f.write(f'{class_index} {x_center:06f} {y_center:06f} {width:06f} {height:06f}\n')
            shutil.copy(input_image_path, output_image_path)


def write_class_txt(class_name_dict):
    class_name_file = BASE_DIR.joinpath('cfg/classes.name')
    with open(class_name_file, mode='w', encoding='utf_8') as f:
        for key in class_name_dict:
            f.write(f'{key}\n')


def show_progress_bar(index, file_path, max_size):
    # progress_bar
    terminal_width = shutil.get_terminal_size().columns
    max_progress_bar_width = 100
    progress_bar_width = min([terminal_width-25, max_progress_bar_width])

    progress_rate = (index+1)/max_size
    progress = int(progress_rate*progress_bar_width)
    progress_bar = '#'*progress + ' '*(progress_bar_width-progress)

    print("\r", f"[{progress_bar}] ({index+1}/{max_size}){file_path.name}", end="")


def make_list_file(data_type, text_paths):
    file_path = BASE_DIR.joinpath(f'cfg/{data_type}.txt')
    with open(file_path, mode='w', encoding='utf_8') as f:
        for text_path in text_paths:
            file_name = text_path.name
            write_path = text_path.parent.parent.parent.joinpath(f'{data_type}/{file_name}')
            f.write(str(write_path)+'\n')


def main(ext='png'):

    class_name_dict = {}

    input_paths = {
        'train': TRAIN_PATH,
        'valid': VALID_PATH,
        'test' : TEST_PATH
    }
    output_paths = {
        'train': OUTPUT_TRAIN_PATH,
        'valid': OUTPUT_VALID_PATH,
        'test' : OUTPUT_TEST_PATH
    }
    count = 0
    for data_type, input_path in input_paths.items():
        track_dir_paths = input_path.glob('track*')
        write_image_paths = []
        for track_dir_path in track_dir_paths:
            image_paths = track_dir_path.glob(f'*.{ext}')
            for image_path in image_paths:
                text_path = get_text_path(image_path, track_dir_path)
                output_path = output_paths[data_type]
                convert2yolo(
                    image_path,
                    text_path,
                    input_path,
                    output_path,
                    class_name_dict,
                    # debag=True
                )
                all_ufpr_files = 4500
                show_progress_bar(count, text_path, all_ufpr_files)
                count += 1
                write_image_paths.append(image_path)
            make_list_file(data_type, write_image_paths)  # debag用にdir毎に書き込む
    write_class_txt(class_name_dict)


if __name__ == '__main__':
    make_output_dir()
    main()
