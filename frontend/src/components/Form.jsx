import { useState } from "react";
import { generatePlan } from "../api";

const INTERESTS = [
  "Culture", "Adventure", "Food", "Nature",
  "Shopping", "History", "Nightlife", "Relaxation",
];

const FOOD_OPTIONS = ["Veg", "Non-Veg", "Both"];

const styles = {
  "@import": "url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap')",
};

export default function Form() {
  const [form, setForm] = useState({
    source: "",
    destination: "",
    budget: "",
    days: 0,
    food: "Veg",
    travelers: 1,
    preferences: [],
  });

  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const step = (key, delta) => {
    const min = 1;
    const max = key === "days" ? 30 : 20;
    setForm((prev) => ({
      ...prev,
      [key]: Math.min(max, Math.max(min, prev[key] + delta)),
    }));
  };

  const togglePref = (pref) => {
    setForm((prev) => ({
      ...prev,
      preferences: prev.preferences.includes(pref)
        ? prev.preferences.filter((p) => p !== pref)
        : [...prev.preferences, pref],
    }));
  };

  const handleSubmit = async () => {
    if (!form.source || !form.destination || !form.budget) {
      setError("Please fill in source, destination, and budget.");
      return;
    }
    setError("");
    setLoading(true);
    setResult("");
    try {
      const data = await generatePlan(form);
      setResult(data.plan);
    } catch (err) {
      setResult("Error generating plan. Please try again.");
    }
    setLoading(false);
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=DM+Sans:wght@300;400;500&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .tp-root {
          font-family: 'DM Sans', sans-serif;
          background: #0f172a;
          min-height: 100vh;
          display: flex;
          justify-content: center;
          align-items: flex-start;
          padding: 2.5rem 1rem 3rem;
        }

        .tp-panel {
          width: 100%;
          max-width: 460px;
        }

        /* ── Header ── */
        .tp-header {
          text-align: center;
          margin-bottom: 2rem;
        }
        .tp-header-rule {
          width: 40px;
          height: 3px;
          background: #C95D3B;
          border-radius: 2px;
          margin: 0 auto 1rem;
        }
        .tp-header h1 {
          font-family: 'Playfair Display', serif;
          font-size: 30px;
          font-weight: 600;
          color: #f1ede4;
          letter-spacing: -0.5px;
          margin-bottom: 4px;
        }
        .tp-header p {
          font-size: 12px;
          font-weight: 300;
          color: #8a8278;
          letter-spacing: 1.5px;
          text-transform: uppercase;
        }

        /* ── Card ── */
        .tp-card {
          background: #1a2336;
          border: 0.5px solid #2a3a56;
          border-radius: 14px;
          padding: 1.25rem 1.25rem 1rem;
          margin-bottom: 10px;
        }

        /* ── Card label ── */
        .tp-card-label {
          font-size: 10px;
          font-weight: 500;
          letter-spacing: 1.8px;
          text-transform: uppercase;
          color: #5a6a84;
          margin-bottom: 14px;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .tp-card-label::after {
          content: '';
          flex: 1;
          height: 0.5px;
          background: #2a3a56;
        }

        /* ── Route row ── */
        .tp-route-row {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          gap: 8px;
          align-items: end;
        }
        .tp-route-arrow {
          font-size: 20px;
          color: #C95D3B;
          text-align: center;
          padding-bottom: 9px;
          line-height: 1;
        }

        /* ── Field ── */
        .tp-field {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .tp-field-label {
          font-size: 11px;
          font-weight: 500;
          color: #6a7a94;
          letter-spacing: 0.3px;
        }
        .tp-input {
          background: #111c2e;
          border: 0.5px solid #2a3a56;
          border-radius: 8px;
          padding: 10px 12px;
          font-family: 'DM Sans', sans-serif;
          font-size: 14px;
          color: #e8e2d8;
          width: 100%;
          outline: none;
          transition: border-color 0.15s;
          -moz-appearance: textfield;
        }
        .tp-input::-webkit-outer-spin-button,
        .tp-input::-webkit-inner-spin-button { -webkit-appearance: none; }
        .tp-input::placeholder { color: #3a4a64; }
        .tp-input:focus { border-color: #C95D3B; }

        /* ── Budget row ── */
        .tp-budget-row {
          display: grid;
          grid-template-columns: auto 1fr;
          gap: 8px;
          align-items: end;
        }
        .tp-currency {
          background: #111c2e;
          border: 0.5px solid #2a3a56;
          border-radius: 8px;
          padding: 10px 12px;
          font-size: 13px;
          font-weight: 500;
          color: #6a7a94;
          white-space: nowrap;
          line-height: 1.5;
        }

        /* ── Meta grid ── */
        .tp-meta-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 8px;
        }

        /* ── Stepper ── */
        .tp-stepper {
          display: flex;
          align-items: center;
          background: #111c2e;
          border: 0.5px solid #2a3a56;
          border-radius: 8px;
          overflow: hidden;
          height: 38px;
        }
        .tp-stepper-btn {
          background: none;
          border: none;
          color: #6a7a94;
          font-size: 18px;
          width: 34px;
          height: 100%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.1s, color 0.1s;
          flex-shrink: 0;
          line-height: 1;
        }
        .tp-stepper-btn:hover {
          background: #1f2f48;
          color: #e8e2d8;
        }
        .tp-stepper-val {
          flex: 1;
          text-align: center;
          font-size: 14px;
          font-weight: 500;
          color: #e8e2d8;
          user-select: none;
        }

        /* ── Food tabs ── */
        .tp-food-tabs {
          display: flex;
          background: #111c2e;
          border: 0.5px solid #2a3a56;
          border-radius: 8px;
          padding: 3px;
          gap: 2px;
          height: 38px;
        }
        .tp-food-tab {
          flex: 1;
          text-align: center;
          font-size: 11px;
          font-weight: 500;
          border-radius: 6px;
          cursor: pointer;
          border: none;
          background: none;
          color: #5a6a84;
          transition: all 0.15s;
          font-family: 'DM Sans', sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .tp-food-tab.active {
          background: #1a2336;
          color: #e8e2d8;
          border: 0.5px solid #3a4a64;
        }

        /* ── Interest chips ── */
        .tp-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .tp-chip {
          padding: 6px 13px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 400;
          cursor: pointer;
          border: 0.5px solid #2a3a56;
          background: #111c2e;
          color: #5a6a84;
          transition: all 0.15s;
          font-family: 'DM Sans', sans-serif;
        }
        .tp-chip.active {
          border-color: #C95D3B;
          background: #2a1610;
          color: #E8936A;
        }

        /* ── Error ── */
        .tp-error {
          font-size: 12px;
          color: #E26B5A;
          margin-bottom: 8px;
          padding: 0 2px;
        }

        /* ── Generate button ── */
        .tp-btn {
          width: 100%;
          padding: 14px;
          background: #C95D3B;
          color: #fff;
          border: none;
          border-radius: 10px;
          font-family: 'Playfair Display', serif;
          font-size: 16px;
          font-weight: 600;
          letter-spacing: 0.3px;
          cursor: pointer;
          transition: opacity 0.15s, transform 0.1s;
          margin-top: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
        }
        .tp-btn:hover:not(:disabled) { opacity: 0.88; }
        .tp-btn:active:not(:disabled) { transform: scale(0.99); }
        .tp-btn:disabled { opacity: 0.55; cursor: not-allowed; }

        /* ── Spinner ── */
        .tp-spinner {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 2px solid rgba(255,255,255,0.35);
          border-top-color: #fff;
          animation: tp-spin 0.7s linear infinite;
          flex-shrink: 0;
        }
        @keyframes tp-spin { to { transform: rotate(360deg); } }

        /* ── Output ── */
        .tp-output {
          background: #1a2336;
          border: 0.5px solid #2a3a56;
          border-radius: 14px;
          padding: 1.25rem;
          margin-top: 10px;
          animation: tp-fadeup 0.35s ease;
        }
        @keyframes tp-fadeup {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .tp-output-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .tp-output-tag {
          font-size: 10px;
          font-weight: 500;
          letter-spacing: 1.5px;
          text-transform: uppercase;
          color: #C95D3B;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .tp-output-dot {
          width: 6px;
          height: 6px;
          background: #C95D3B;
          border-radius: 50%;
        }
        .tp-output-meta {
          font-size: 11px;
          color: #5a6a84;
        }
        .tp-output-body {
          font-size: 13px;
          line-height: 1.8;
          color: #a0aaba;
          white-space: pre-wrap;
          font-family: 'DM Sans', sans-serif;
        }
      `}</style>

      <div className="tp-root">
        <div className="tp-panel">

          {/* Header */}
          <div className="tp-header">
            <div className="tp-header-rule" />
            <h1>Travel Planner</h1>
            <p>Craft your perfect journey</p>
          </div>

          {/* Route */}
          <div className="tp-card">
            <div className="tp-card-label">Route</div>
            <div className="tp-route-row">
              <div className="tp-field">
                <div className="tp-field-label">From</div>
                <input
                  className="tp-input"
                  name="source"
                  placeholder="e.g. Chennai"
                  value={form.source}
                  onChange={handleChange}
                />
              </div>
              <div className="tp-route-arrow">→</div>
              <div className="tp-field">
                <div className="tp-field-label">To</div>
                <input
                  className="tp-input"
                  name="destination"
                  placeholder="e.g. Paris"
                  value={form.destination}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          {/* Budget */}
          <div className="tp-card">
            <div className="tp-card-label">Budget</div>
            <div className="tp-budget-row">
              <div className="tp-currency">₹ INR</div>
              <div className="tp-field" style={{ flex: 1 }}>
                <input
                  className="tp-input"
                  name="budget"
                  type="number"
                  placeholder="e.g. 80000"
                  min="0"
                  value={form.budget}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          {/* Trip Details */}
          <div className="tp-card">
            <div className="tp-card-label">Trip Details</div>
            <div className="tp-meta-grid">

              {/* Days stepper */}
              <div className="tp-field">
                <div className="tp-field-label">Days</div>
                <div className="tp-stepper">
                  <button className="tp-stepper-btn" onClick={() => step("days", -1)}>−</button>
                  <span className="tp-stepper-val">{form.days}</span>
                  <button className="tp-stepper-btn" onClick={() => step("days", 1)}>+</button>
                </div>
              </div>

              {/* Travelers stepper */}
              <div className="tp-field">
                <div className="tp-field-label">Travelers</div>
                <div className="tp-stepper">
                  <button className="tp-stepper-btn" onClick={() => step("travelers", -1)}>−</button>
                  <span className="tp-stepper-val">{form.travelers}</span>
                  <button className="tp-stepper-btn" onClick={() => step("travelers", 1)}>+</button>
                </div>
              </div>

              {/* Food tabs */}
              <div className="tp-field">
                <div className="tp-field-label">Food</div>
                <div className="tp-food-tabs">
                  {FOOD_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      className={`tp-food-tab${form.food === opt ? " active" : ""}`}
                      onClick={() => setForm({ ...form, food: opt })}
                    >
                      {opt === "Non-Veg" ? "Non-V" : opt}
                    </button>
                  ))}
                </div>
              </div>

            </div>
          </div>

          {/* Interests */}
          <div className="tp-card">
            <div className="tp-card-label">Interests</div>
            <div className="tp-chips">
              {INTERESTS.map((pref) => (
                <button
                  key={pref}
                  className={`tp-chip${form.preferences.includes(pref) ? " active" : ""}`}
                  onClick={() => togglePref(pref)}
                >
                  {pref}
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && <div className="tp-error">{error}</div>}

          {/* Submit */}
          <button className="tp-btn" onClick={handleSubmit} disabled={loading}>
            {loading ? (
              <>
                <div className="tp-spinner" />
                Generating...
              </>
            ) : (
              "Plan My Journey →"
            )}
          </button>

          {/* Output */}
          {result && (
            <div className="tp-output">
              <div className="tp-output-header">
                <div className="tp-output-tag">
                  <span className="tp-output-dot" />
                  Your Itinerary
                </div>
                <div className="tp-output-meta">
                  {form.days} days · {form.travelers} pax · ₹{Number(form.budget).toLocaleString("en-IN")}
                </div>
              </div>
              <div className="tp-output-body">{result}</div>
            </div>
          )}

        </div>
      </div>
    </>
  );
}
