import http from "k6/http";
import { SharedArray } from "k6/data";
import { check } from "k6";

const questions = new SharedArray("user questions", function () {
  return JSON.parse(open("./cf-user-questions.json"));
});

export default function () {
  // randomly pick one query:
  const q = questions[Math.floor(Math.random() * questions.length)];

  const req = http.get(q, { tags: { name: "ask" } });

  check(req, {
    "is status 200": (r) => r.status === 200,
  });
  if (req.status === 200) {
    const res = req.json();
    // console.log(res.answer_text, q)
    check(res, {
      "has no errors": (r) => "errors" in r === false,
      //	    'has an answer': (r) => r.answer_text && r.answer_text.length > 2,
    });
  } else {
    console.error(req.status, req.text, req.body, q);
  }
}
