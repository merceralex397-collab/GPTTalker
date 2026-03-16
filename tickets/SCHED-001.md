# SCHED-001: Task classification

## Summary

Implement the task classification system that categorizes incoming LLM requests into routing classes. Define routing classes (quick_classification, summarization, embeddings, code_analysis, long_form_reasoning, coding_agent) and build a classifier that determines the appropriate class for each request, using rules or a helper model.

## Stage

planning

## Status

todo

## Depends On

- CORE-006

## Acceptance Criteria

- [ ] Routing class enum: quick_classification, summarization, embeddings, code_analysis, long_form_reasoning, coding_agent
- [ ] Rule-based classifier: classify by tool name, prompt length, explicit hints
- [ ] Optional helper-model classifier: use a fast LLM for ambiguous cases
- [ ] Classification metadata: class, confidence, reasoning
- [ ] Explicit class override parameter (user can force a routing class)
- [ ] Classification logging for analysis and tuning
- [ ] Classifier is pluggable (swap rule-based for model-based without code changes)
- [ ] Unit tests for each routing class with sample inputs

## Artifacts

- None yet

## Notes

- Rule-based classifier should be the default — fast, predictable, no external dependency
- Helper model classifier is optional enhancement for ambiguous cases
- Classification drives routing decisions in SCHED-002
- Consider adding confidence thresholds: high confidence → auto-route, low → ask user
