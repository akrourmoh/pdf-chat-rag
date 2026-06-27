def format_sources(chunks):
    # This function takes the chunk records that were used to answer a question
    # and builds a short, de-duplicated list of human-readable source labels
    # like "report.pdf (p.4)". The order is preserved (most relevant first) and
    # duplicates are removed, so the user sees a clean list of citations.

    labels = []
    for chunk in chunks:
        label = f"{chunk['source']} (p.{chunk['page']})"
        if label not in labels:
            labels.append(label)
    return labels
