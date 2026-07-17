import { getShowcaseScenario, SHOWCASE_SCENARIOS } from "@/lib/showcase/fixtures";
import { initialShowcaseState, showcaseReducer } from "@/lib/showcase/reducer";

describe("showcase", () => {
  it("defines all approved deterministic experiences", () => {
    expect(Object.keys(SHOWCASE_SCENARIOS)).toEqual(["knowledge", "aurasql", "analysis", "career"]);
  });

  it("rejects unknown route input", () => expect(getShowcaseScenario("billing")).toBeNull());

  it("advances one step at a time and clamps at the end", () => {
    const scenario = getShowcaseScenario("knowledge")!;
    let state = initialShowcaseState(scenario);
    state = showcaseReducer(state, { type: "advance" });
    expect(state.activeStep).toBe(1);
    for (let index = 0; index < 20; index += 1) state = showcaseReducer(state, { type: "advance" });
    expect(state.activeStep).toBe(scenario.steps.length - 1);
    expect(state.status).toBe("complete");
  });

  it("restarts without retaining simulated output state", () => {
    const scenario = getShowcaseScenario("aurasql")!;
    const advanced = showcaseReducer(initialShowcaseState(scenario), { type: "advance" });
    expect(showcaseReducer(advanced, { type: "restart" })).toEqual(initialShowcaseState(scenario));
  });
});
