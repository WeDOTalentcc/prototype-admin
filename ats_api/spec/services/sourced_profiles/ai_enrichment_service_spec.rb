# frozen_string_literal: true

require 'rails_helper'

RSpec.describe SourcedProfiles::AiEnrichmentService, type: :service do
  let(:account) { create(:account) }
  let(:sourced_profile) { create(:sourced_profile, account: account, skills_data: [], expertise: [], profile_data: {}) }
  let(:sourcing) { create(:sourcing, account: account) }

  let(:sourced_profile_sourcing) do
    create(
      :sourced_profile_sourcing,
      sourced_profile: sourced_profile,
      sourcing: sourcing,
      account: account,
      analysis: sample_analysis
    )
  end

  let(:sample_analysis) do
    {
      "calculated_score" => 85,
      "score_confidence" => "high",
      "one_liner" => "Experienced Ruby developer with strong backend skills",
      "skills_assessment" => {
        "strong" => [ "Ruby", "Rails", "PostgreSQL", "Redis" ],
        "mentioned" => [ "Docker", "AWS", "React" ]
      },
      "highlights" => [
        { "type" => "technical_depth", "description" => "Solid experience with Ruby on Rails ecosystem" },
        { "type" => "career_progression", "description" => "Fast progression to senior developer position" }
      ],
      "development_areas" => [
        { "type" => "skill_gap", "description" => "Could improve cloud infrastructure knowledge", "requirement" => "Cloud Computing" }
      ],
      "suggested_questions" => [
        "Describe your experience scaling Rails applications",
        "How do you approach database optimization?"
      ],
      "evaluation" => [
        { "requirement" => "Backend Development", "match_level" => "exceeds", "priority" => "essential", "points" => 95, "rationale" => "Strong backend" }
      ]
    }
  end

  describe '#enrich!' do
    subject(:service) { described_class.new(sourced_profile_sourcing) }

    it 'creates skills from analysis' do
      expect { service.enrich! }.to change { Skill.count }.by(7)
    end

    it 'creates skill relationships' do
      expect { service.enrich! }.to change { SkillRelationship.count }.by(7)
    end

    it 'sets level 3 for strong skills' do
      service.enrich!

      ruby_skill = Skill.find_by(name: "Ruby", account: account)
      relationship = SkillRelationship.find_by(skill: ruby_skill, reference: sourced_profile)

      expect(relationship.level_skill).to eq(3)
    end

    it 'sets level 2 for mentioned skills' do
      service.enrich!

      docker_skill = Skill.find_by(name: "Docker", account: account)
      relationship = SkillRelationship.find_by(skill: docker_skill, reference: sourced_profile)

      expect(relationship.level_skill).to eq(2)
    end

    it 'populates skills_data with skill entries' do
      service.enrich!

      skills = sourced_profile.reload.skills_data
      expect(skills.size).to eq(7)

      ruby_entry = skills.find { |s| s["name"] == "Ruby" }
      expect(ruby_entry["level"]).to eq("strong")
      expect(ruby_entry["source"]).to eq("ai_analysis")

      docker_entry = skills.find { |s| s["name"] == "Docker" }
      expect(docker_entry["level"]).to eq("mentioned")
    end

    it 'adds skill names to expertise as strings only' do
      service.enrich!

      expertise = sourced_profile.reload.expertise
      expect(expertise).to all(be_a(String))
      expect(expertise).to include("Ruby", "Rails", "PostgreSQL")
      expect(expertise.size).to eq(7)
    end

    it 'enriches profile_data with highlights, questions, evaluation' do
      service.enrich!

      data = sourced_profile.reload.profile_data
      expect(data["highlights"]).to be_present
      expect(data["suggested_questions"]).to include("Describe your experience scaling Rails applications")
      expect(data["development_areas"]).to be_present
      expect(data["evaluation"]).to be_present
      expect(data["enrichment"]["skills_extracted"]).to eq(7)
    end

    it 'sets summary from one_liner when blank' do
      service.enrich!

      expect(sourced_profile.reload.summary).to eq("Experienced Ruby developer with strong backend skills")
    end

    it 'does not overwrite existing summary' do
      sourced_profile.update!(summary: "Existing summary")
      service.enrich!

      expect(sourced_profile.reload.summary).to eq("Existing summary")
    end

    it 'does not duplicate skills_data on multiple runs' do
      service.enrich!
      first_count = sourced_profile.reload.skills_data.size

      described_class.new(sourced_profile_sourcing.reload).enrich!
      expect(sourced_profile.reload.skills_data.size).to eq(first_count)
    end

    it 'does not duplicate expertise on multiple runs' do
      service.enrich!
      first_count = sourced_profile.reload.expertise.size

      described_class.new(sourced_profile_sourcing.reload).enrich!
      expect(sourced_profile.reload.expertise.size).to eq(first_count)
    end

    it 'does not duplicate skill relationships' do
      service.enrich!
      expect { described_class.new(sourced_profile_sourcing.reload).enrich! }.not_to change { SkillRelationship.count }
    end

    context 'when skill already exists' do
      let!(:existing_skill) { create(:skill, name: "Ruby", account: account) }

      it 'reuses existing skill' do
        expect { service.enrich! }.to change { Skill.count }.by(6)
      end

      it 'creates relationship with existing skill' do
        service.enrich!

        relationship = SkillRelationship.find_by(skill: existing_skill, reference: sourced_profile)
        expect(relationship).to be_present
      end
    end

    context 'when analysis is empty' do
      let(:sourced_profile_sourcing) do
        create(:sourced_profile_sourcing, sourced_profile: sourced_profile, sourcing: sourcing, account: account, analysis: {})
      end

      it 'does not create skills' do
        expect { service.enrich! }.not_to change { Skill.count }
      end

      it 'does not modify skills_data' do
        service.enrich!
        expect(sourced_profile.reload.skills_data).to be_empty
      end
    end

    context 'when analysis has nil values' do
      let(:sample_analysis) do
        {
          "calculated_score" => 70,
          "skills_assessment" => nil,
          "highlights" => nil,
          "development_areas" => nil
        }
      end

      it 'handles gracefully without errors' do
        expect { service.enrich! }.not_to raise_error
      end
    end

    context 'when skills_assessment contains non-string values' do
      let(:sample_analysis) do
        {
          "calculated_score" => 85,
          "skills_assessment" => {
            "strong" => [ "Ruby", 123, { "name" => "Rails" }, nil, "" ],
            "mentioned" => [ "Docker" ]
          },
          "highlights" => []
        }
      end

      it 'filters out non-string and blank values' do
        service.enrich!

        skill_names = sourced_profile.reload.skills_data.map { |s| s["name"] }
        expect(skill_names).to contain_exactly("Ruby", "Docker")
      end
    end

    context 'when profile already has skills_data' do
      let(:sourced_profile) do
        create(:sourced_profile, account: account, skills_data: [ { "name" => "Ruby", "level" => "expert" } ], expertise: [ "Ruby" ], profile_data: {})
      end

      it 'does not duplicate existing skills in skills_data' do
        service.enrich!

        ruby_entries = sourced_profile.reload.skills_data.select { |s| s["name"]&.downcase == "ruby" }
        expect(ruby_entries.size).to eq(1)
      end

      it 'does not duplicate existing expertise entries' do
        service.enrich!

        ruby_entries = sourced_profile.reload.expertise.select { |e| e.is_a?(String) && e.downcase == "ruby" }
        expect(ruby_entries.size).to eq(1)
      end
    end
  end
end
