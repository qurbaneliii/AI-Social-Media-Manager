import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    generate_load: {
      executor: "constant-vus",
      vus: 100,
      duration: "1m"
    }
  }
};

const payload = JSON.stringify({
  company_id: "00000000-0000-0000-0000-000000000001",
  post_intent: "announce",
  core_message: "ARIA launch campaign for multichannel social growth and conversion uplift.",
  target_platforms: ["linkedin", "x"],
  campaign_tag: "spring_launch",
  manual_keywords: ["ai", "growth"],
  urgency_level: "scheduled"
});

export default function () {
  const response = http.post("http://localhost:4000/v1/posts/generate", payload, {
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer test-token"
    }
  });

  check(response, {
    "status is 200 or 201": (r) => r.status === 200 || r.status === 201
  });
}
