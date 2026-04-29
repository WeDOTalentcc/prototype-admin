# frozen_string_literal: true

module Wsi
  module BloomLevels
    LABEL_TO_NUM = {
      "remember" => 1,
      "lembrar" => 1,
      "understand" => 2,
      "compreender" => 2,
      "apply" => 3,
      "aplicar" => 3,
      "analyze" => 4,
      "analisar" => 4,
      "evaluate" => 5,
      "avaliar" => 5,
      "create" => 6,
      "criar" => 6
    }.freeze

    module_function

    def from_question(value)
      return nil if value.blank?

      s = value.to_s.strip.downcase
      return s.to_i if s.match?(/\A[1-6]\z/)

      LABEL_TO_NUM[s] || LABEL_TO_NUM[s.split.first] || infer_from_partial(s)
    end

    def infer_from_partial(s)
      return 4 if s.include?("analy")
      return 3 if s.include?("appl")
      return 6 if s.include?("creat")
      return 5 if s.include?("eval")
      return 2 if s.include?("understand")
      return 1 if s.include?("remember")

      nil
    end
  end
end
