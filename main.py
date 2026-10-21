from config import INPUT, OUTPUT

from pipeline import process_folder


def main(input_dir=INPUT, output_dir=OUTPUT):

    process_folder(input_dir, output_dir)


if __name__ == "__main__":
    main()
