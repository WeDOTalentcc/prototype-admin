# frozen_string_literal: true

module Llm
  class UsageTracker
    Result = Struct.new(
      :response,
      :model,
      :input_tokens,
      :output_tokens,
      :total_tokens,
      :cost_usd,
      :latency_ms,
      :success,
      keyword_init: true
    )

    def initialize(
      model:,
      operation:,
      user: nil,
      account: nil,
      context: {}
    )
      @model = model
      @operation = operation
      @user = user
      @account = account
      @context = context
    end

    def track
      start_time = Time.current
      response = nil
      error = nil

      begin
        response = yield
        extract_and_save_metrics(response, start_time, success: true)
        response
      rescue => e
        error = e
        extract_and_save_metrics(nil, start_time, success: false, error: e)
        raise
      end
    end

    private

    attr_reader :model, :operation, :user, :account, :context

    def extract_and_save_metrics(response, start_time, success:, error: nil)
      latency_ms = ((Time.current - start_time) * 1000).round(2)

      if success && response
        usage = extract_usage(response)
        cost = CostCalculator.calculate(
          model: model,
          input_tokens: usage[:input_tokens],
          output_tokens: usage[:output_tokens]
        )

        save_cost_record(
          input_tokens: usage[:input_tokens],
          output_tokens: usage[:output_tokens],
          total_tokens: usage[:total_tokens],
          cost: cost,
          latency_ms: latency_ms,
          success: true
        )
      else
        save_cost_record(
          input_tokens: 0,
          output_tokens: 0,
          total_tokens: 0,
          cost: 0.0,
          latency_ms: latency_ms,
          success: false,
          error_message: error&.message
        )
      end
    end

    def extract_usage(response)
      usage = response.dig("usage") || {}

      {
        input_tokens: usage["prompt_tokens"] || usage["promptTokenCount"] || 0,
        output_tokens: usage["completion_tokens"] || usage["candidatesTokenCount"] || 0,
        total_tokens: usage["total_tokens"] || usage["totalTokenCount"] || 0
      }
    end

    def save_cost_record(
      input_tokens:,
      output_tokens:,
      total_tokens:,
      cost:,
      latency_ms:,
      success:,
      error_message: nil
    )
      return unless user && account

      LlmUsage.create!(
        user: user,
        account: account,
        model: model,
        operation: operation,
        input_tokens: input_tokens,
        output_tokens: output_tokens,
        total_tokens: total_tokens,
        cost_usd: cost,
        latency_ms: latency_ms,
        success: success,
        error_message: error_message,
        context: context
      )
    rescue => e
      Rails.logger.error "[LLM::UsageTracker] Failed to save metrics: #{e.message}"
    end
  end
end
