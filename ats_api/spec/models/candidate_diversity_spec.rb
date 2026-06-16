require "rails_helper"

RSpec.describe Candidate, type: :model do
  describe "diversity fields" do
    it "has ethnicity enum with 6 values" do
      expect(Candidate.ethnicities.keys).to match_array(
        %w[white black brown yellow indigenous undeclared]
      )
    end

    it "defaults boolean diversity fields to false" do
      candidate = build(:candidate)
      expect(candidate.pcd).to be false
      expect(candidate.lgbtqia).to be false
      expect(candidate.neurodivergent).to be false
      expect(candidate.is_hidden).to be false
      expect(candidate.is_twin).to be false
    end
  end

  describe "scopes" do
    let!(:visible)   { create(:candidate, is_hidden: false) }
    let!(:hidden)    { create(:candidate, is_hidden: true) }
    let!(:expired)   { create(:candidate, lgpd_expires_at: 1.day.ago) }
    let!(:valid_ttl) { create(:candidate, lgpd_expires_at: 30.days.from_now) }
    let!(:null_ttl)  { create(:candidate, lgpd_expires_at: nil) }

    it ".visible excludes hidden" do
      expect(Candidate.visible).to include(visible)
      expect(Candidate.visible).not_to include(hidden)
    end

    it ".lgpd_active excludes expired, includes null and future" do
      result = Candidate.lgpd_active
      expect(result).to include(valid_ttl, null_ttl)
      expect(result).not_to include(expired)
    end
  end

  describe "twin association" do
    it "links to twin_source via belongs_to" do
      source = create(:candidate)
      twin = create(:candidate, is_twin: true, twin_source_id: source.id)
      expect(twin.twin_source).to eq(source)
    end
  end
end
