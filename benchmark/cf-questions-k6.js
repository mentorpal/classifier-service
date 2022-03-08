/*
This software is Copyright ©️ 2020 The University of Southern California. All Rights Reserved.
Permission to use, copy, modify, and distribute this software and its documentation for educational, research and non-profit purposes, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and subject to the full license file found in the root of this software deliverable. Permission to make commercial use of this software may be obtained by contacting:  USC Stevens Center for Innovation University of Southern California 1150 S. Olive Street, Suite 2300, Los Angeles, CA 90115, USA Email: accounting@stevens.usc.edu

The full terms of this copyright and license should always be found in the root directory of this software deliverable as "license.txt" and if these terms are not found with this software, please contact the USC Stevens Center for the full license.
*/
import http from "k6/http";
import { SharedArray } from "k6/data";
import { check } from "k6";

const apiUrl =
  "https://api.mentorpal.org/classifier/questions/?referer=load-test";
const questions = new SharedArray("user questions", function () {
  return JSON.parse(open("./cf-questions.json"));
});
const mentors = [
  "610dad8c16e879e3c3c6f711",
  "610dd3f616e879e3c3d88818",
  "610e854f16e879e3c32ea550",
  "610e860416e879e3c32efbd4",
  "6114286e16e879e3c3b97ad7",
  "61294b1854f809684401e4be",
  "61294d8a54f80968440320df",
  "612e636c54f80968446cb57c",
  "614394d406c21f1afa434db7",
  "614398e306c21f1afa459f56",
  "6144bc7d06c21f1afaeb59a4",
  "6153ae754be7d1a8ecc1e8f3",
  "615fdc4eae00075f6f163d2c",
  "6171b620c7ea4df5a68702db",
  "6172fdfac7ea4df5a660385d",
  "61796622c7ea4df5a61febd1",
  "61843084c7ea4df5a62c6f21",
  "618ebc9ac7ea4df5a6616712",
  "619c22d3836e4af90c8fc131",
  "61b20a97836e4af90c0df4b6",
  "61ba2ef59e733a8a0eb8c3dd",
  "61c2435f9e733a8a0e25ce1b",
  "620ab98bd2e9412da30d7c3e",
];
export default function () {
  // randomly pick one mentor and question:
  const q = questions[Math.floor(Math.random() * questions.length)];
  const m = mentors[Math.floor(Math.random() * mentors.length)];
  const url = `${apiUrl}&mentor=${m}&query=${encodeURIComponent(q)}`;
  const req = http.get(url.toString(), { tags: { name: "ask" } });

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
    console.log(req.status, req.text, req.body, m, q);
    console.log(url.toString());
  }
}
