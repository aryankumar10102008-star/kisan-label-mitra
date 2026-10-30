# Kisan Label Mitra – Vanilla HTML, CSS and JavaScript

This is a framework-free conversion of the supplied v0/Next.js frontend prototype.

## Run locally
1. Extract this ZIP.
2. Open the extracted folder in VS Code.
3. Open the terminal in this folder.
4. Run `python -m http.server 3000`.
5. Visit `http://localhost:3000`.

You can also open `index.html` directly, but a local server is recommended.

## Files
- `index.html` – page structure and screens
- `style.css` – responsive styling
- `app.js` – language toggle, photo preview, screen flow, demo results and speech

## What works
- Hindi is the default language; English can be selected.
- Camera capture hint and gallery image selection.
- Selected image preview.
- Crop name and spray date fields.
- Loading, result and error screen layouts.
- Sample toxicity/crop/harvest/label explanations.
- Browser text-to-speech where supported.

## Important: this is still a frontend demo
The uploaded photo is **not** sent to OCR, an AI model, or a backend. After a short loading delay, the app displays one of four hard-coded sample results. The error screen is present but no real OCR failure can trigger it yet.

The sample pesticide names and all toxicity, dosage, crop, PPE, and waiting-period content are demonstration content only. They have not been verified against an actual product label or an authoritative source. **Do not use this demo output to decide what to spray, how much to spray, what protective equipment to use, or when to harvest.** The real app must extract the exact label and verify safety-critical information before presenting it as guidance.

## Next development step
Connect the Read label action to a backend OCR + label-understanding service. The backend should return structured fields with source text and confidence/verification status. Do not let the frontend invent missing safety information.
