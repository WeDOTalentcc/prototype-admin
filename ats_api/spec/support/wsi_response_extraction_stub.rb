# frozen_string_literal: true

def stub_wsi_response_extraction(overrides = {})
  base = {
    star_components: { situation: true, task: true, action: true, result: true },
    trait_signals_detected: [
      "action — excerpt: \"implementei automação\"",
      "result — excerpt: \"redução de 30%\""
    ],
    trait_signals_absent: [],
    rationale: [],
    bloom_demonstrated: 4,
    bloom_label: "Analisar",
    dreyfus_demonstrated: 3,
    dreyfus_label: "Competent",
    inflation_detected: false,
    inflation_evidence: "",
    specificity_score: 7,
    key_quote: "\"implementei automação\"",
    response_authentic: true,
    authenticity_concern: nil,
    _llm_fallback: false
  }
  allow(Wsi::ResponseExtractorService).to receive(:call).and_return(
    Wsi::ResponseExtractorService::Result.new(
      success?: true,
      data: base.merge(overrides),
      error: nil,
      raw_response: "{}"
    )
  )
end
