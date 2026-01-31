import dspy
import pandas as pd
from typing import Literal
import json
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential

# ----------------------------------------------------------------
# 0. LM CONFIGURATIE
# ----------------------------------------------------------------

load_dotenv()

credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default").token

lm = dspy.LM(
    model=os.getenv("MODEL_DEPLOYMENT_NAME"),
    api_base=os.getenv("ENDPOINT"),
    api_key=token,
    api_version="2024-10-21"
)
dspy.configure(lm=lm)

# ----------------------------------------------------------------
# 1. LABELS LADEN
# ----------------------------------------------------------------

with open("labels.json", encoding="utf-8") as f:
    config = json.load(f)

LABELS = config["labels"]
CONTACT_REASONS = list(LABELS.keys())

def build_label_descriptions() -> str:
    """Bouw label beschrijvingen voor de signature."""
    return "\n".join([
        f"- {key}: {info['description']}" 
        for key, info in LABELS.items()
    ])


# ----------------------------------------------------------------
# 2. SIGNATURE DEFINITIE
# ----------------------------------------------------------------

class ContactReasonSignature(dspy.Signature):
    """Classificeer een klant email naar de meest passende contact reden voor."""
    
    subject: str = dspy.InputField(desc="Het onderwerp van de email")
    first_message: str = dspy.InputField(desc="Het eerste klantbericht")
    
    contact_reason: Literal[tuple(CONTACT_REASONS)] = dspy.OutputField(
        desc=f"De categorie die het beste past bij het probleem van de klant.\n\nCategorieën:\n{build_label_descriptions()}"
    )

# ----------------------------------------------------------------
# 3. CLASSIFIER MODULE
# ----------------------------------------------------------------

class EmailClassifier(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict(ContactReasonSignature)

    def forward(self, subject: str, first_message: str):
        return self.predictor(subject=subject, first_message=first_message)

# ----------------------------------------------------------------
# 4. DATASET VOORBEREIDEN
# ----------------------------------------------------------------

def prepare_dataset(df: pd.DataFrame):
    """Converteer DataFrame naar DSPy Examples."""
    dataset = []
    for _, row in df.iterrows():
        example = dspy.Example(
            subject=row['subject'] or "",
            first_message=row['first_message'] or "",
            contact_reason=row['contact_reason']
        ).with_inputs('subject', 'first_message')
        dataset.append(example)
    return dataset

# ----------------------------------------------------------------
# 5. MAIN
# ----------------------------------------------------------------

if __name__ == "__main__":
    
    # Initialiseer classifier
    classifier = EmailClassifier()
    
    # Laad dataset
    df = pd.read_parquet("../data/ticket_details_clean.parquet")
    print(f"✓ {len(df)} tickets geladen")
    
    df_prepared = prepare_dataset(df)
    
    # Test met een realistisch Order Delay voorbeeld uit de dataset
    pred = classifier(
        subject="Re: Belangrijk nieuws over je bestelling #19984",
        first_message="Ik heb nog niks mogen ontvangen"
    )
    print(f"Predicted: {pred.contact_reason}")