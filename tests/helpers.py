from __future__ import annotations

from contextlib import nullcontext

from minuteflow.schemas import ExtractionOutput, SourceDocument, VerificationOutput


class ScriptedBackend:
    def __init__(
        self,
        *,
        extractions: list[ExtractionOutput],
        verifications: list[VerificationOutput],
    ) -> None:
        self.extractions = list(extractions)
        self.verifications = list(verifications)
        self.extract_calls = 0
        self.verify_calls = 0
        self.feedback_received: list[str | None] = []

    def trace_context(self):
        return nullcontext()

    async def extract(
        self, document: SourceDocument, *, feedback: str | None = None
    ) -> ExtractionOutput:
        del document
        self.extract_calls += 1
        self.feedback_received.append(feedback)
        return self.extractions.pop(0)

    async def verify(
        self, document: SourceDocument, extraction: ExtractionOutput
    ) -> VerificationOutput:
        del document, extraction
        self.verify_calls += 1
        return self.verifications.pop(0)
