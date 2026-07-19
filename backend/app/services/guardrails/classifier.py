from transformers import pipeline
from app.core.config import settings

UNSAFE_INPUT_MESSAGE = "Your message contained content that violates our safety guidelines. Please rephrase your question."
UNSAFE_OUTPUT_MESSAGE = "The generated response violated our safety policies and could not be displayed."


class GuardrailsClassifier:
    def __init__(self, model_name: str | None = None, threshold: float | None = None):
        self.model_name = model_name or settings.GUARDRAILS_MODEL
        self.threshold = threshold or settings.GUARDRAILS_THRESHOLD
        self._classifier = None

    @property
    def classifier(self):
        if self._classifier is None:
            try:
                self._classifier = pipeline("text-classification", model=self.model_name)
            except Exception:
                self._classifier = lambda text: [{"label": "clean", "score": 0.0}]
        return self._classifier

    def is_safe(self, text: str) -> bool:
        if not text or not text.strip():
            return True

        try:
            results = self.classifier(text[:512])
            if not results:
                return True

            label_data = results[0]
            label = str(label_data.get("label", "")).lower()
            score = float(label_data.get("score", 0.0))

            if ("toxic" in label or "hate" in label or "label_1" in label or "bad" in label) and score >= self.threshold:
                return False
            return True
        except Exception:
            return True


_classifier_instance: GuardrailsClassifier | None = None


def get_guardrails_classifier() -> GuardrailsClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = GuardrailsClassifier()
    return _classifier_instance
