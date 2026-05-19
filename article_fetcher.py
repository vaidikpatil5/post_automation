import trafilatura


def fetch_full_article(article_url):
    try:
        downloaded = trafilatura.fetch_url(article_url)

        if not downloaded:
            print("Trafilatura fetch failed: no HTML returned")
            return ""

        extracted = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
            output_format="txt",
        )

        if not extracted:
            print("Trafilatura extraction failed: no article text extracted")
            return ""

        return extracted[:25000]
    except Exception as e:
        print(f"Full article fetch error: {e}")
        return ""
