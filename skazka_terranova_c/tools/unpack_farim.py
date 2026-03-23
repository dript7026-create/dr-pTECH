import argparse
from pathlib import Path
from zipfile import ZipFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    with ZipFile(input_path, 'r') as archive:
        archive.extractall(output_path)

    print(f'Extracted {input_path} -> {output_path}')


if __name__ == '__main__':
    main()
