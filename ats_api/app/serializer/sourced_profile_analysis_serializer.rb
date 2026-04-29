class SourcedProfileAnalysisSerializer
  def initialize(sourced_profile:, analysis:)
    @sourced_profile = sourced_profile
    @analysis = analysis
  end

  def as_json
    {
      data: @analysis.merge(
        sourced_profile_id: @sourced_profile.id,
        cached_at: Time.current.iso8601,
        cache_ttl_seconds: SourcedProfileAnalysisService::CACHE_TTL.to_i
      ),
      meta: { source: "llm", model: SourcedProfileAnalysisService::MODEL_HINT }
    }
  end
end
