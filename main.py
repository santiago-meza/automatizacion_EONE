from config import INPUT, OUTPUT

from pipeline import process_folder


def main():

    process_folder(INPUT, OUTPUT)


if __name__ == "__main__":
    main()
