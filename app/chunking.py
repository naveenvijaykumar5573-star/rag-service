import re


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
):
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    paragraphs = re.split(r"\n\s*\n", text)

    paragraphs = [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]

    chunks = []
    current_paragraphs = []
    current_length = 0

    for paragraph in paragraphs:

        paragraph_length = len(paragraph)

        # Add paragraph if it fits
        if (
            current_paragraphs
            and current_length + paragraph_length + 2 > chunk_size
        ):
            chunks.append("\n\n".join(current_paragraphs))

            # Keep the last paragraph as overlap
            overlap_paragraph = current_paragraphs[-1]

            current_paragraphs = [overlap_paragraph]
            current_length = len(overlap_paragraph)

        current_paragraphs.append(paragraph)
        current_length += (
            paragraph_length
            if len(current_paragraphs) == 1
            else paragraph_length + 2
        )

    if current_paragraphs:
        chunks.append("\n\n".join(current_paragraphs))

    return chunks