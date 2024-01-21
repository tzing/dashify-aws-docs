# Dashify AWS Docs

Generate [Kapeli Dash] (or [Zeal]) docset from AWS documentation.

[Kapeli Dash]: https://kapeli.com/dash
[Zeal]: https://zealdocs.org/


## Prerequisites

- Python 3.11+
- wget

This script does not handle downloading the documentation.
We're using `wget` to download the documentation. See [Usage](#usage) for more details.


## Currently Supported Documentation

- [Redshift Database Developer Guide](https://docs.aws.amazon.com/redshift/latest/dg/index.html)


## Usage

1. Clone this repository

   ```bash
   git clone git@github.com:tzing/dashify-aws-docs.git
   ```

2. Install dependencies with [Poetry] and activate the virtual environment

   ```bash
   poetry install
   poetry shell
   ```

   [Poetry]: https://python-poetry.org/

3. Download AWS documentation using `wget`

   ```bash
   wget <SITE_MAP_URL> -O- \
     | dashify extract-sitemap-urls
     | wget --recursive --no-clobber --no-parent --page-requisites --input-file=-
   ```

   See [site maps](#site-maps) table below for the URL of supported documentation.

4. Run the corresponding script

   ```bash
   dashify <SERVICE> -u <SITE_URL> -r <ROOT_DIR> -d <DOCSET_PATH>
   ```

   - `SERVICE`: The AWS service name. Currently only `redshift` is supported.
   - `SITE_URL`: The URL of the documentation site. For example, `https://docs.aws.amazon.com/redshift/latest/dg/`.
   - `ROOT_DIR`: Root directory that contains the downloaded docs. It's default to `./docs.aws.amazon.com` and you do not need to specify it if you're using the `wget` command above.
   - `DOCSET_PATH`: The output path of the generated docset. For example, `./redshift-developer-guide.docset`.

   For example, to generate a Traditional Chinese (zh_TW) docset for Redshift:

   ```bash
   dashify redshift \
       -u https://docs.aws.amazon.com/zh_tw/redshift/latest/dg/ \
       -d redshift-developer-guide.docset
   ```

The script will generate a docset at the specified output path.


## Site Maps

### Redshift Database Developer Guide

| Language | URL                                                                |
| -------- | ------------------------------------------------------------------ |
| `de_DE`  | `https://docs.aws.amazon.com/de_de/redshift/latest/dg/sitemap.xml` |
| `en_US`  | `https://docs.aws.amazon.com/redshift/latest/dg/sitemap.xml`       |
| `es_ES`  | `https://docs.aws.amazon.com/es_es/redshift/latest/dg/sitemap.xml` |
| `fr_FR`  | `https://docs.aws.amazon.com/fr_fr/redshift/latest/dg/sitemap.xml` |
| `id_ID`  | `https://docs.aws.amazon.com/id_id/redshift/latest/dg/sitemap.xml` |
| `it_IT`  | `https://docs.aws.amazon.com/it_it/redshift/latest/dg/sitemap.xml` |
| `ja_JP`  | `https://docs.aws.amazon.com/ja_jp/redshift/latest/dg/sitemap.xml` |
| `ko_KR`  | `https://docs.aws.amazon.com/ko_kr/redshift/latest/dg/sitemap.xml` |
| `pt_BR`  | `https://docs.aws.amazon.com/pt_br/redshift/latest/dg/sitemap.xml` |
| `zh_CN`  | `https://docs.aws.amazon.com/zh_cn/redshift/latest/dg/sitemap.xml` |
| `zh_TW`  | `https://docs.aws.amazon.com/zh_tw/redshift/latest/dg/sitemap.xml` |
