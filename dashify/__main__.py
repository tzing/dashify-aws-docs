import tqdm.contrib.logging

import dashify.redshift
import dashify.sitemap
from dashify.core import entry

if __name__ == "__main__":
    with tqdm.contrib.logging.logging_redirect_tqdm():
        dashify.core.dashify_entry()
