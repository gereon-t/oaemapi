import os
import urllib.request
import xmltodict


def main():
    download_folder = "lod2-data"

    if not os.path.exists(download_folder):
        os.mkdir(download_folder)

    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/3dg/lod2_gml/lod2_gml/"

    page = urllib.request.urlopen(base_url)
    xml_data = xmltodict.parse(page.read())

    if "opengeodata" not in xml_data:
        raise Exception("Invalid XML data")

    for dataset in xml_data["opengeodata"]["datasets"].values():
        if "files" not in dataset:
            continue

        for files in dataset["files"].values():
            for file in files:
                filename = file["@name"]
                urllib.request.urlretrieve(
                    base_url + filename, os.path.join(download_folder, filename)
                )


if __name__ == "__main__":
    main()
