from app.retriever import retrieve_chunks
from app.llm import generate_answer


TENANT_ID = "7b93c62c-b74f-41da-bb97-3a8da5a674a5"

DOCUMENT_ID = "e577efc0-744e-421a-b27c-488598ffaadd"


def run_rag(question: str):

    results = retrieve_chunks(
        question=question,
        tenant_id=TENANT_ID,
        document_id=DOCUMENT_ID,
        top_k=3
    )

    if not results:
        return None, []

    retrieval_context = [
        row[4]
        for row in results
    ]

    context = "\n\n".join(retrieval_context)

    answer = generate_answer(
        question,
        context
    )

    return answer, retrieval_context


def test_relevant_question_returns_answer():

    question = "What is this document about?"

    answer, context = run_rag(question)

    assert answer is not None
    assert answer.strip() != ""

    assert len(context) > 0

    print("\nANSWER:")
    print(answer)


def test_out_of_context_question():

    question = "Who is the Prime Minister of India?"

    answer, context = run_rag(question)

    assert answer is not None

    expected = "I don't know based on the provided documents."

    assert expected in answer

    print("\nOUT-OF-CONTEXT ANSWER:")
    print(answer)


def test_retrieval_returns_chunks():

    question = "What is this document about?"

    answer, context = run_rag(question)

    assert len(context) > 0
    assert len(context) <= 3

    print("\nRETRIEVED CHUNKS:", len(context))