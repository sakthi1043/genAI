import { useState, useRef, useEffect } from "react";

// ============= ITINERARY COMPONENTS =============

function StatCard({ label, value, color = "#B87333" }) {
  return (
    <div style={{
      background: `linear-gradient(135deg, ${color}15 0%, ${color}08 100%)`,
      border: `2px solid ${color}30`,
      borderRadius: 16,
      padding: "20px 16px",
      textAlign: "center",
      flex: 1,
      cursor: "pointer",
      transition: "all 0.3s ease",
      boxShadow: "0 4px 12px rgba(0,0,0,0.05)",
      position: "relative",
      overflow: "hidden",
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = "translateY(-4px)";
      e.currentTarget.style.boxShadow = `0 8px 20px ${color}25`;
      e.currentTarget.style.borderColor = `${color}60`;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = "translateY(0)";
      e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.05)";
      e.currentTarget.style.borderColor = `${color}30`;
    }}
    >
      <div style={{ 
        fontSize: "0.65rem", 
        color: "#9B9490", 
        textTransform: "uppercase", 
        letterSpacing: "0.08em", 
        marginBottom: 8,
        fontWeight: 600
      }}>
        {label}
      </div>
      <div style={{ 
        fontSize: "1.5rem", 
        fontWeight: 700, 
        color, 
        fontFamily: "'DM Sans', sans-serif",
        lineHeight: 1.2
      }}>
        {value}
      </div>
    </div>
  );
}

function FlightCard({ flight }) {
  if (!flight || !flight.airline) return null;
  return (
    <div style={{
      background: "linear-gradient(135deg, #B87333 0%, #A85A1E 100%)",
      borderRadius: 16,
      padding: "24px",
      marginBottom: 24,
      boxShadow: "0 8px 24px rgba(184,115,51,0.2)",
      border: "1px solid rgba(255,255,255,0.1)",
      color: "#fff",
      position: "relative",
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute",
        top: -40,
        right: -40,
        width: 120,
        height: 120,
        background: "rgba(255,255,255,0.05)",
        borderRadius: "50%",
      }} />
      <div style={{ 
        fontSize: "0.75rem", 
        color: "rgba(255,255,255,0.9)", 
        textTransform: "uppercase", 
        letterSpacing: "0.08em", 
        marginBottom: 12,
        fontWeight: 700,
        opacity: 0.9
      }}>
        Flight Information
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>{flight.airline}</div>
          <div style={{ fontSize: "0.8rem", opacity: 0.8, marginTop: 4 }}>Duration: {flight.duration}</div>
          {flight.departure && (
            <div style={{ fontSize: "0.75rem", opacity: 0.7, marginTop: 2 }}>Departure: {flight.departure}</div>
          )}
        </div>
        <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>
          {typeof flight.price === "number" ? `₹${flight.price.toLocaleString("en-IN")}` : flight.price}
        </div>
      </div>
    </div>
  );
}

function AccommodationCard({ accommodation }) {
  if (!accommodation || !accommodation.name) return null;
  return (
    <div style={{
      background: "#FFFDF9",
      border: "2px solid #4ECDC430",
      borderRadius: 16,
      padding: "20px",
      marginBottom: 24,
    }}>
      <div style={{ 
        fontSize: "0.75rem", 
        textTransform: "uppercase", 
        letterSpacing: "0.08em", 
        marginBottom: 12,
        fontWeight: 700,
        color: "#4ECDC4"
      }}>
        Accommodation
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#1A1814" }}>{accommodation.name}</div>
          {accommodation.location && (
            <div style={{ fontSize: "0.8rem", color: "#8C887F", marginTop: 4 }}>{accommodation.location}</div>
          )}
          {accommodation.amenities && (
            <div style={{ fontSize: "0.78rem", color: "#9B9490", marginTop: 4 }}>{accommodation.amenities}</div>
          )}
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#4ECDC4" }}>
            {typeof accommodation.pricePerNight === "number" ? `₹${accommodation.pricePerNight.toLocaleString("en-IN")}` : accommodation.pricePerNight}
            <span style={{ fontSize: "0.7rem", fontWeight: 400, color: "#8C887F" }}>/night</span>
          </div>
          {accommodation.rating && (
            <div style={{ fontSize: "0.75rem", color: "#8C887F", marginTop: 4 }}>Rating: {accommodation.rating}/5</div>
          )}
        </div>
      </div>
    </div>
  );
}

function DayCard({ dayNum, title, activities }) {
  const [expanded, setExpanded] = useState(false);
  const colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#C7B3E5"];
  const dayColor = colors[dayNum % colors.length];

  const dayTotal = (activities || []).reduce((sum, a) => sum + (a.cost || 0), 0);

  return (
    <div style={{ marginBottom: 16 }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: "100%",
          background: expanded ? dayColor : "#FFFDF9",
          color: expanded ? "#fff" : "#1A1814",
          border: `2px solid ${dayColor}40`,
          borderRadius: expanded ? "16px 16px 0 0" : 16,
          padding: "18px 20px",
          textAlign: "left",
          cursor: "pointer",
          fontSize: "0.95rem",
          fontWeight: 700,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          transition: "all 0.3s ease",
          fontFamily: "'DM Sans', sans-serif",
          boxShadow: expanded ? `0 6px 16px ${dayColor}25` : "0 2px 8px rgba(0,0,0,0.05)",
          textTransform: "uppercase",
          letterSpacing: "0.02em",
        }}
      >
        <span>Day {dayNum}: {title}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ 
            fontSize: "0.8rem", 
            fontWeight: 600,
            opacity: 0.9,
            textTransform: "none",
          }}>
            {dayTotal > 0 ? `₹${dayTotal.toLocaleString("en-IN")}` : ""}
          </span>
          <span style={{ 
            fontSize: "1.3rem", 
            transition: "transform 0.3s ease", 
            transform: expanded ? "rotate(180deg)" : "rotate(0deg)" 
          }}>&#9660;</span>
        </div>
      </button>

      {expanded && (
        <div style={{
          background: "linear-gradient(to bottom, #FFFDF9 0%, #FAF3E8 100%)",
          border: `2px solid ${dayColor}40`,
          borderTop: "none",
          borderBottomLeftRadius: 16,
          borderBottomRightRadius: 16,
          padding: "24px 20px",
          marginTop: 0,
          boxShadow: `0 6px 16px ${dayColor}15`,
        }}>
          {(activities || []).map((activity, i) => (
            <div key={i} style={{ 
              marginBottom: i < activities.length - 1 ? 20 : 0,
              padding: "16px",
              background: "#fff",
              borderRadius: 12,
              borderLeft: `4px solid ${dayColor}`,
              boxShadow: "0 2px 8px rgba(0,0,0,0.03)",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = `0 4px 12px ${dayColor}20`;
              e.currentTarget.style.transform = "translateX(4px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.03)";
              e.currentTarget.style.transform = "translateX(0)";
            }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                <div>
                  <span style={{ 
                    fontSize: "0.7rem", 
                    fontWeight: 700, 
                    textTransform: "uppercase",
                    color: dayColor,
                    letterSpacing: "0.05em"
                  }}>
                    {activity.timeSlot || ""}
                  </span>
                  {activity.time && (
                    <span style={{ fontSize: "0.72rem", color: "#8C887F", marginLeft: 8 }}>
                      {activity.time}
                    </span>
                  )}
                </div>
                <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#B87333" }}>
                  {typeof activity.cost === "number" ? `₹${activity.cost.toLocaleString("en-IN")}` : `₹${activity.cost || 0}`}
                </span>
              </div>
              <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "#1A1814", marginBottom: 4 }}>
                {activity.activity || activity.place || "Activity"}
              </div>
              {activity.place && activity.activity && (
                <div style={{ fontSize: "0.78rem", color: "#5A5650", marginBottom: 4 }}>
                  {activity.place}
                </div>
              )}
              {activity.meal && (
                <div style={{ fontSize: "0.78rem", color: "#5A5650", marginBottom: 4 }}>
                  {activity.meal}
                </div>
              )}
              {activity.details && (
                <div style={{ fontSize: "0.78rem", color: "#8C887F", lineHeight: 1.5 }}>
                  {activity.details}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BudgetBreakdown({ budget }) {
  if (!budget) return null;

  const items = [
    { label: "Flights", amount: budget.flights || 0, color: "#FF6B6B" },
    { label: "Accommodation", amount: budget.accommodation || 0, color: "#4ECDC4" },
    { label: "Food & Dining", amount: budget.food || 0, color: "#FFE66D" },
    { label: "Activities", amount: budget.activities || 0, color: "#95E1D3" },
    { label: "Transport", amount: budget.transport || 0, color: "#A8D8EA" },
    { label: "Buffer", amount: budget.buffer || 0, color: "#C7B3E5" },
  ].filter(item => item.amount > 0);

  const total = budget.total || items.reduce((s, item) => s + item.amount, 0);

  return (
    <div style={{ marginTop: 32 }}>
      <div style={{ 
        fontSize: "1rem", 
        fontWeight: 700, 
        color: "#1A1814", 
        marginBottom: 16,
        display: "flex",
        alignItems: "center",
        gap: 8
      }}>
        Budget Breakdown
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12 }}>
        {items.map((item, i) => {
          const pct = total > 0 ? Math.round((item.amount / total) * 100) : 0;
          return (
            <div key={i} style={{
              padding: "16px",
              background: `linear-gradient(135deg, ${item.color}15 0%, ${item.color}08 100%)`,
              borderRadius: 12,
              borderLeft: `5px solid ${item.color}`,
              transition: "all 0.3s ease",
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(0,0,0,0.03)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = `0 6px 16px ${item.color}20`;
              e.currentTarget.style.transform = "translateY(-2px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.03)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#1A1814" }}>
                  {item.label}
                </div>
                <div style={{ fontSize: "1rem", fontWeight: 700, color: item.color }}>
                  {`₹${item.amount.toLocaleString("en-IN")}`}
                </div>
              </div>
              <div style={{ 
                height: 8, 
                background: "#fff", 
                borderRadius: 4, 
                overflow: "hidden",
                border: `1px solid ${item.color}20`
              }}>
                <div style={{
                  height: "100%",
                  background: `linear-gradient(90deg, ${item.color} 0%, ${item.color}dd 100%)`,
                  width: `${pct}%`,
                  transition: "width 0.6s ease",
                  borderRadius: 4,
                }} />
              </div>
              <div style={{ fontSize: "0.7rem", color: "#8C887F", marginTop: 8, fontWeight: 600 }}>
                {pct}% of total
              </div>
            </div>
          );
        })}
      </div>
      <div style={{
        marginTop: 24,
        padding: "20px 24px",
        background: "linear-gradient(135deg, #B87333 0%, #A85A1E 100%)",
        borderRadius: 16,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        boxShadow: "0 8px 24px rgba(184,115,51,0.25)",
        color: "#fff",
      }}>
        <div style={{ fontSize: "0.95rem", color: "rgba(255,255,255,0.9)", fontWeight: 600 }}>Total Trip Cost</div>
        <div style={{ fontSize: "1.6rem", fontWeight: 800, fontFamily: "'DM Sans', sans-serif" }}>
          {`₹${total.toLocaleString("en-IN")}`}
        </div>
      </div>
    </div>
  );
}

function TipsSection({ tips }) {
  if (!tips || tips.length === 0) return null;
  return (
    <div style={{ marginTop: 28 }}>
      <div style={{ 
        fontSize: "1rem", 
        fontWeight: 700, 
        color: "#1A1814", 
        marginBottom: 12
      }}>
        Travel Tips
      </div>
      <div style={{ 
        background: "#FFFDF9", 
        border: "2px solid #95E1D330", 
        borderRadius: 12, 
        padding: "16px 20px" 
      }}>
        {tips.map((tip, i) => (
          <div key={i} style={{ 
            fontSize: "0.82rem", 
            color: "#5A5650", 
            padding: "8px 0",
            borderBottom: i < tips.length - 1 ? "1px solid rgba(0,0,0,0.05)" : "none",
            lineHeight: 1.5
          }}>
            {tip}
          </div>
        ))}
      </div>
    </div>
  );
}

function ItineraryDisplay({ data }) {
  // data is the parsed JSON object from the backend
  const tripDetails = data.tripDetails || {};
  const flight = data.flight || {};
  const accommodation = data.accommodation || {};
  const days = data.days || [];
  const budget = data.budget || {};
  const tips = data.tips || [];

  return (
    <div style={{
      background: "#FFFDF9",
      borderRadius: 20,
      padding: "32px",
      border: "1px solid rgba(184,115,51,0.08)",
      marginBottom: 16,
      boxShadow: "0 10px 32px rgba(0,0,0,0.06)",
    }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ 
          fontSize: "1.6rem", 
          fontWeight: 800, 
          background: "linear-gradient(135deg, #B87333 0%, #A85A1E 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          marginBottom: 8,
          letterSpacing: "-0.02em"
        }}>
          Your Perfect Itinerary
        </div>
        <div style={{ 
          fontSize: "0.9rem", 
          color: "#9B9490",
          fontWeight: 500,
          lineHeight: 1.6
        }}>
          {tripDetails.source && tripDetails.destination 
            ? `${tripDetails.source} to ${tripDetails.destination} - ${tripDetails.days || days.length} days`
            : "Personalized travel plan with activities, dining, and accommodations"}
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 32 }}>
        <StatCard label="Duration" value={tripDetails.days ? `${tripDetails.days} days` : `${days.length} days`} color="#FF6B6B" />
        <StatCard label="Travelers" value={tripDetails.travelers || "N/A"} color="#4ECDC4" />
        <StatCard label="Budget" value={tripDetails.totalBudget ? `₹${tripDetails.totalBudget.toLocaleString("en-IN")}` : "N/A"} color="#FFE66D" />
        <StatCard label="Daily Budget" value={tripDetails.dailyBudget ? `₹${tripDetails.dailyBudget.toLocaleString("en-IN")}` : "N/A"} color="#95E1D3" />
      </div>

      {/* Flight */}
      <FlightCard flight={flight} />

      {/* Accommodation */}
      <AccommodationCard accommodation={accommodation} />

      {/* Days Itinerary */}
      <div style={{ marginTop: 32, marginBottom: 32 }}>
        <div style={{ 
          fontSize: "1.1rem", 
          fontWeight: 700, 
          color: "#1A1814", 
          marginBottom: 18,
          display: "flex",
          alignItems: "center",
          gap: 10
        }}>
          Day by Day Breakdown
          <span style={{
            fontSize: "0.7rem",
            background: "#E8D5B0",
            color: "#B87333",
            padding: "4px 10px",
            borderRadius: 999,
            fontWeight: 600
          }}>
            {days.length} DAYS
          </span>
        </div>
        {days.map((day, i) => (
          <DayCard 
            key={i} 
            dayNum={day.dayNumber || i + 1} 
            title={day.title || `Day ${i + 1}`} 
            activities={day.activities || []} 
          />
        ))}
      </div>

      {/* Budget */}
      <BudgetBreakdown budget={budget} />

      {/* Tips */}
      <TipsSection tips={tips} />
    </div>
  );
}

const QUICK_TRIPS = [
  { src: "Mumbai", dest: "Goa" },
  { src: "Delhi", dest: "Jaipur" },
  { src: "Bangalore", dest: "Ooty" },
  { src: "Chennai", dest: "Pondicherry" },
  { src: "Hyderabad", dest: "Hampi" },
  { src: "Kolkata", dest: "Darjeeling" },
];

function Avatar({ role }) {
  return (
    <div
      style={{
        width: 36,
        height: 36,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: role === "bot" ? "1rem" : "0.7rem",
        fontWeight: 500,
        flexShrink: 0,
        fontFamily: role === "bot" ? "'Playfair Display', serif" : "inherit",
        fontStyle: role === "bot" ? "italic" : "normal",
        background: role === "bot" ? "#E8D5B0" : "#E1EFEB",
        color: role === "bot" ? "#B87333" : "#2D6A5A",
      }}
    >
      {role === "bot" ? "W" : "You"}
    </div>
  );
}

function TypingBubble() {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
      <Avatar role="bot" />
      <div
        style={{
          background: "#FFFDF9",
          border: "1px solid rgba(26,24,20,0.08)",
          borderRadius: "16px 16px 16px 4px",
          padding: "14px 18px",
        }}
      >
        <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
          {[0, 0.2, 0.4].map((delay, i) => (
            <div
              key={i}
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "#B87333",
                animation: `bounce 1.2s ${delay}s infinite`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Message({ role, text, planData }) {
  // If this is a structured itinerary response
  if (planData && planData.format === "json" && role === "bot") {
    return (
      <div style={{
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
        animation: "fadeUp 0.35s ease forwards",
        opacity: 0,
        width: "100%",
      }}>
        <Avatar role={role} />
        <div style={{ flex: 1 }}>
          <ItineraryDisplay data={planData.data} />
        </div>
      </div>
    );
  }

  // Regular text message
  const displayText = typeof text === "string" ? text : JSON.stringify(text, null, 2);
  
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
        flexDirection: role === "user" ? "row-reverse" : "row",
        animation: "fadeUp 0.35s ease forwards",
        opacity: 0,
        width: "100%",
      }}
    >
      <Avatar role={role} />
      <div
        style={{
          maxWidth: "75%",
          padding: "12px 16px",
          borderRadius:
            role === "bot" ? "16px 16px 16px 4px" : "16px 16px 4px 16px",
          fontSize: "0.835rem",
          lineHeight: 1.7,
          background: role === "bot" ? "#FFFDF9" : "#B87333",
          border:
            role === "bot" ? "1px solid rgba(26,24,20,0.08)" : "none",
          color: role === "bot" ? "#1A1814" : "#fff",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {displayText}
      </div>
    </div>
  );
}

function WelcomeCard() {
  return (
    <div
      style={{
        background: "#FAF3E8",
        border: "1px solid #E8D5B0",
        borderRadius: 16,
        padding: "1.5rem",
        textAlign: "center",
      }}
    >
      <h2
        style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: "1.3rem",
          fontWeight: 600,
          marginBottom: "0.4rem",
          color: "#1A1814",
        }}
      >
        Where would you like to go?
      </h2>
      <p style={{ fontSize: "0.82rem", color: "#8C887F", lineHeight: 1.6 }}>
        Fill in your trip details on the left and I'll plan a complete
        day-by-day itinerary with real places, hotels, food, and a full budget
        breakdown.
      </p>
    </div>
  );
}

export default function App() {
  const [src, setSrc] = useState("");
  const [dest, setDest] = useState("");
  const [budget, setBudget] = useState("");
  const [days, setDays] = useState("");
  const [travelers, setTravelers] = useState("");
  const [food, setFood] = useState("");
  const [messages, setMessages] = useState([]);
  const [chatText, setChatText] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastRequest, setLastRequest] = useState(null);
  const [sessionId, setSessionId] = useState("default");
  const messagesRef = useRef(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const addMsg = (role, text, planData = null) =>
    setMessages((prev) => [...prev, { role, text, planData, id: Date.now() + Math.random() }]);

  const submitPlan = async () => {
    if (!src || !dest || !budget || !days || !travelers || !food) {
      addMsg("bot", "Please fill in all fields before generating your itinerary.");
      return;
    }

    const req = {
      source: src,
      destination: dest,
      budget: parseInt(budget),
      days: parseInt(days),
      food,
      travelers: parseInt(travelers),
    };
    setLastRequest(req);
    
    // Create a unique session ID for this trip
    const newSessionId = `${src}-${dest}-${Date.now()}`;
    setSessionId(newSessionId);

    addMsg(
      "user",
      `Plan a ${days}-day trip from ${src} to ${dest} for ${travelers} traveler(s) with ₹${parseInt(budget).toLocaleString("en-IN")} budget. Food: ${food}.`
    );
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });
      const data = await res.json();
      
      const plan = data.plan;
      
      if (plan && plan.format === "json") {
        // Structured JSON response - display as itinerary cards
        addMsg("bot", "", plan);
      } else if (plan && plan.format === "text") {
        // Text fallback
        addMsg("bot", plan.data || "Something went wrong. Please try again.");
      } else if (typeof plan === "string") {
        // Legacy string response
        addMsg("bot", plan);
      } else {
        addMsg("bot", "Something went wrong. Please try again.");
      }
    } catch (err) {
      addMsg(
        "bot",
        `Could not connect to the backend.\n\nMake sure your FastAPI server is running at http://localhost:8000\n\nError: ${err.message}`
      );
    } finally {
      setLoading(false);
    }
  };

  const sendChat = async () => {
    const text = chatText.trim();
    if (!text || loading) return;
    setChatText("");
    addMsg("user", text);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: sessionId
        }),
      });
      const data = await res.json();
      addMsg("bot", data.response || "No response received. Try again.");
    } catch (err) {
      addMsg(
        "bot",
        `Could not connect to chatbot service.\n\nMake sure your FastAPI server is running at http://localhost:8000\n\nError: ${err.message}`
      );
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: "0.875rem",
    color: "#1A1814",
    background: "#F8F5EE",
    border: "1px solid rgba(184,115,51,0.25)",
    borderRadius: 8,
    padding: "9px 12px",
    outline: "none",
    width: "100%",
    appearance: "none",
  };

  const labelStyle = {
    fontSize: "0.68rem",
    fontWeight: 500,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "#8C887F",
    display: "block",
    marginBottom: 5,
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #F8F5EE; }
        
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
        
        @keyframes fadeUp {
          from { 
            opacity: 0; 
            transform: translateY(20px); 
          }
          to { 
            opacity: 1; 
            transform: translateY(0); 
          }
        }
        
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        
        input:focus, select:focus {
          border-color: #B87333 !important;
          background: #FAF3E8 !important;
          box-shadow: 0 0 0 3px rgba(184,115,51,0.1);
          transition: all 0.2s ease;
        }
        
        ::-webkit-scrollbar { 
          width: 6px; 
        }
        
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        
        ::-webkit-scrollbar-thumb { 
          background: rgba(184,115,51,0.3); 
          border-radius: 3px;
          transition: background 0.2s ease;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(184,115,51,0.5);
        }
        
        button:active {
          transform: scale(0.98);
        }
      `}</style>

      <div style={{ fontFamily: "'DM Sans', sans-serif", minHeight: "100vh", display: "flex", flexDirection: "column", background: "#F8F5EE" }}>
        {/* Header */}
        <header style={{
          background: "#FFFDF9",
          borderBottom: "1px solid rgba(184,115,51,0.18)",
          padding: "0 2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 64,
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}>
          <div style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.5rem", fontWeight: 600, letterSpacing: "-0.02em" }}>
            Wand<span style={{ color: "#B87333", fontStyle: "italic" }}>r</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#2D6A5A", animation: "pulse 2s infinite" }} />
            <span style={{ fontSize: "0.72rem", color: "#8C887F", letterSpacing: "0.06em", textTransform: "uppercase" }}>
              AI Planner Online
            </span>
          </div>
        </header>

        {/* Shell */}
        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "320px 1fr", maxWidth: 1200, margin: "0 auto", width: "100%" }}>
          {/* Sidebar */}
          <aside style={{
            background: "#FFFDF9",
            borderRight: "1px solid rgba(26,24,20,0.08)",
            padding: "2rem 1.5rem",
            display: "flex",
            flexDirection: "column",
            gap: "1.25rem",
          }}>
            <div>
              <div style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.05rem", fontWeight: 600, marginBottom: 4 }}>Plan Your Journey</div>
              <div style={{ fontSize: "0.78rem", color: "#8C887F", lineHeight: 1.5 }}>Fill in the details and let the AI craft your perfect itinerary.</div>
            </div>

            <hr style={{ border: "none", borderTop: "1px solid rgba(26,24,20,0.08)" }} />

            <div><label style={labelStyle}>From</label>
              <input style={inputStyle} value={src} onChange={e => setSrc(e.target.value)} placeholder="e.g. Mumbai" />
            </div>

            <div><label style={labelStyle}>To</label>
              <input style={inputStyle} value={dest} onChange={e => setDest(e.target.value)} placeholder="e.g. Goa" />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div><label style={labelStyle}>Days</label>
                <input style={inputStyle} type="number" min="1" max="30" value={days} onChange={e => setDays(e.target.value)} placeholder="5" />
              </div>
              <div><label style={labelStyle}>Travelers</label>
                <input style={inputStyle} type="number" min="1" value={travelers} onChange={e => setTravelers(e.target.value)} placeholder="2" />
              </div>
            </div>

            <div><label style={labelStyle}>Total Budget (INR)</label>
              <input style={inputStyle} type="number" value={budget} onChange={e => setBudget(e.target.value)} placeholder="25000" />
            </div>

            <div>
              <label style={labelStyle}>Food Preference</label>
              <div style={{ position: "relative" }}>
                <select style={{ ...inputStyle, paddingRight: 28 }} value={food} onChange={e => setFood(e.target.value)}>
                  <option value="">Select preference</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="non-vegetarian">Non-Vegetarian</option>
                  <option value="vegan">Vegan</option>
                  <option value="any">Any</option>
                </select>
                <span style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", fontSize: "0.7rem", color: "#8C887F", pointerEvents: "none" }}>&#9662;</span>
              </div>
            </div>

            <button
              onClick={submitPlan}
              disabled={loading}
              style={{
                background: loading ? "#8C887F" : "#B87333",
                color: "#fff",
                border: "none",
                borderRadius: 10,
                padding: "12px",
                fontFamily: "'DM Sans', sans-serif",
                fontSize: "0.9rem",
                fontWeight: 500,
                cursor: loading ? "not-allowed" : "pointer",
                transition: "background 0.2s",
                letterSpacing: "0.01em",
              }}
            >
              {loading ? "Planning..." : "Generate Itinerary"}
            </button>

            <hr style={{ border: "none", borderTop: "1px solid rgba(26,24,20,0.08)" }} />

            <div>
              <div style={{ fontSize: "0.78rem", color: "#8C887F", marginBottom: 8 }}>Quick destinations</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {QUICK_TRIPS.map((t) => (
                  <button
                    key={t.src + t.dest}
                    onClick={() => { setSrc(t.src); setDest(t.dest); }}
                    style={{
                      fontSize: "0.72rem",
                      padding: "4px 10px",
                      borderRadius: 999,
                      border: "1px solid rgba(184,115,51,0.2)",
                      background: "#F8F5EE",
                      color: "#4A4640",
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                      fontFamily: "'DM Sans', sans-serif",
                    }}
                  >
                    {t.src} to {t.dest}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          {/* Chat */}
          <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)", overflow: "hidden" }}>
            <div ref={messagesRef} style={{ flex: 1, overflowY: "auto", padding: "2rem 2.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {/* Welcome */}
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <Avatar role="bot" />
                <WelcomeCard />
              </div>

              {messages.map((m) => (
                <Message key={m.id} role={m.role} text={m.text} planData={m.planData} />
              ))}

              {loading && <TypingBubble />}
            </div>

            {/* Input bar */}
            <div style={{
              borderTop: "1px solid rgba(26,24,20,0.08)",
              padding: "1rem 2rem",
              background: "#FFFDF9",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}>
              <input
                value={chatText}
                onChange={e => setChatText(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") sendChat(); }}
                placeholder="Ask a follow-up question..."
                style={{
                  flex: 1,
                  fontFamily: "'DM Sans', sans-serif",
                  fontSize: "0.9rem",
                  background: "#F8F5EE",
                  border: "1px solid rgba(184,115,51,0.25)",
                  borderRadius: 10,
                  padding: "10px 14px",
                  outline: "none",
                  color: "#1A1814",
                }}
              />
              <button
                onClick={sendChat}
                disabled={loading}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: loading ? "#8C887F" : "#B87333",
                  border: "none",
                  cursor: loading ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  transition: "background 0.2s",
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#fff">
                  <path d="M2 21L23 12 2 3v7l15 2-15 2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
