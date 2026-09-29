from rag.retriever import search_clinical_guidance
from rag.service import retrieve_context




def test_supported_patient_record_question_is_grounded():

    result = retrieve_context(
        "Can AI modify a patient's medical record?"
    )

    assert result.grounded is True
    assert result.top_score is not None
    assert result.top_score >= 0.40

    normalized_context = " ".join(result.context.split())

    assert "modify the patient record" in normalized_context

    assert "clinical_guidelines.txt" in result.sources

def test_supported_patient_access_question_is_grounded():

    result = retrieve_context(

        "Who can access patient information?"

    )

    assert result.grounded is True

    assert result.top_score is not None

    assert result.top_score >= 0.40

    assert "authenticated users" in result.context

def test_vacation_policy_is_not_grounded():

    result = retrieve_context(

        "What is the organization's vacation policy?"

    )

    assert result.grounded is False

    assert result.context == ""

    assert result.sources == []

def test_unrelated_question_is_not_grounded():

    result = retrieve_context(

        "Who won the Super Bowl?"

    )

    assert result.grounded is False

    assert result.context == ""

    assert result.sources == []
def test_retrieves_patient_record_policy():

    results = search_clinical_guidance(
        "Can AI modify a patient's medical record?"
    )

    assert len(results) > 0

    combined = " ".join(
        result["content"].lower()
        for result in results
    )

    assert "modify" in combined
    assert "patient record" in combined


def test_results_include_source():

    results = search_clinical_guidance(
        "What are the rules for patient data access?"
    )

    assert len(results) > 0

    assert results[0]["source"] == "clinical_guidelines.txt"