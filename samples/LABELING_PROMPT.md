# Labeling prompt for a separate chat

You are independently annotating 100 patent-family abstracts for a humanoid-robot patent relevance study (Electrolux). I am uploading random_100_for_labeling.csv. All 100 abstracts are originally written in English; no machine translation has been performed. The columns are docdb_family_id, abstract_language and abstract.

Judge ALL 100 records using ONLY the supplied abstract. Use docdb_family_id only as a key. Do not use CPC, title, applicant, external searches, guesses about potential applications, or any decision-model predictions.

## Binary relevance definition

- label=1: The abstract explicitly and substantively concerns a humanoid, human-shaped, or anthropomorphic embodied robot, or a component/control/locomotion/manipulation/perception system specifically designed for humanoid robots. Use semantic meaning, not keyword matching.
- label=0: The abstract does not establish that connection. Generic robotic arms/hands, generic AI/control/vision, appliances, industrial robots and standalone sensors/actuators are not relevant merely because humanoids could use them.
- needs_review=1: The abstract is ambiguous, too vague, or lacks essential context to decide reliably. In that case leave label empty, explain why and do NOT guess.

All input abstracts are English. Quote exact English text from each source abstract. Do not translate, edit the input, invent technical details, or infer an unsupported humanoid application.

## Required deliverable

Create a downloadable UTF-8 CSV file named humanoid_100_manual_labels.csv with EXACTLY these columns:

    docdb_family_id,label,needs_review,confidence,evidence_quote,reason

Write exactly one row for every input family, in the same order. label is 1, 0, or empty only when needs_review=1. needs_review is 0 or 1. confidence is high, medium or low (annotation confidence, not a model probability). evidence_quote is a brief exact excerpt from the abstract (preferably 5–20 original words); reason is one concise explanation grounded in the abstract.

Before finalizing, verify: 100 rows; 100 unique IDs; same IDs and order as input; valid fields; no missing records; no contradictory label/review values. Report counts for labels 1, 0 and needs_review, including reasons for any unresolved cases. Do not silently resolve questionable records. If creating a file is impossible, provide complete CSV text in a code block.

These are AI-assisted provisional labels, not independent human gold labels. The researcher will verify all ambiguous examples and review a selection of clear cases before using them to calibrate/evaluate the decision model.
