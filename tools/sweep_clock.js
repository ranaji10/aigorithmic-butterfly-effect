// The clock of the sweep. A copy, for the record: the running one lives outside this repository, as a Cloudflare
// Worker named abe-sweep-clock in the author's account, with one trigger (cron "23 * * * *") and one secret
// (GITHUB_TOKEN: a fine-grained GitHub token for this repository only, Actions: read and write, nothing else).
//
// Why it exists: GitHub runs a scheduled workflow "when it has room" and on a quiet repository drops most chances
// (17 November 2026: one sweep in seven hours with six chances an hour). A workflow started through the API runs
// within seconds. So once an hour this clock asks GitHub to start .github/workflows/sweep.yml, and does nothing else.
// The schedule inside sweep.yml stays as the second clock, for the day this one stops.
//
// It holds no key to anything but "start a workflow of this repository", it reads nothing, and nobody can make it
// tick from outside: the address answers 404 and only the trigger calls tick().
// If it stops (the token has an end date; see SECURITY.md): make a new token, replace the secret, nothing else.
// To replace the clock itself: anything that can send one HTTPS request an hour will do.

const WORKFLOW = "https://api.github.com/repos/ranaji10/aigorithmic-butterfly-effect/actions/workflows/sweep.yml";

function ask(env, method, path, body) {
  return fetch(WORKFLOW + path, {
    method,
    headers: {
      "Authorization": "Bearer " + env.GITHUB_TOKEN,
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "abe-sweep-clock",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

async function tick(env) {
  let r = await ask(env, "POST", "/dispatches", { ref: "main" });
  if (!r.ok && r.status !== 401 && r.status !== 403) {
    // GitHub switches a scheduled workflow off after sixty days without a commit. Switch it on again, ask once more.
    await ask(env, "PUT", "/enable");
    r = await ask(env, "POST", "/dispatches", { ref: "main" });
  }
  if (!r.ok) throw new Error("GitHub answered " + r.status + " to the clock of the sweep");
}

export default {
  async scheduled(event, env, ctx) {
    await tick(env);
  },
  async fetch() {
    return new Response("The clock of the sweep of AIgorithmic Butterfly Effect. It only ticks.", {
      status: 404,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  },
};
