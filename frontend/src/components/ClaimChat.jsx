import React, { useState } from "react";
import { generateAdjusterBrief } from "../api/claims";

function ChatBotUI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    const userMessage = { sender: "user", text: input };
    setMessages(prev => [...prev, userMessage]);

    // For testing: Use mock claim JSON until your full pipeline is ready
    const mockClaimData = {
      incident: {
        date: "2025-11-13",
        location: "SZR Dubai",
        description: "Rear-end collision"
      },
      damage: {
        areas: ["rear bumper", "right tail light"],
        severity: "medium"
      },
      policy: {
        coverage_limit: "2500 USD",
        type: "Collision"
      },
      decision: {
        payout: 1500,
        risk_score: "LOW",
        flags: []
      }
    };

    // Call backend only when user requests the adjuster brief
    if (input.toLowerCase().includes("adjuster brief")) {
      const result = await generateAdjusterBrief(mockClaimData);
      const botMessage = {
        sender: "bot",
        text: result.adjuster_brief
      };
      setMessages(prev => [...prev, botMessage]);
    }

    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((m, idx) => (
          <div key={idx} className={`message ${m.sender}`}>
            {m.text}
          </div>
        ))}
      </div>

      <div className="input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type 'generate adjuster brief' to test"
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default ChatBotUI;
