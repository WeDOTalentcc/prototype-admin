# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::LinkedinDataProcessor do
  let(:account) { create(:account) }
  let(:candidate) { create(:candidate, account: account) }
  let(:linkedin_data) { {} }
  let(:processor) { described_class.new(candidate, linkedin_data) }

  describe '#process_all' do
    let(:linkedin_data) do
      {
        'basic_info' => {
          'name' => 'John Doe',
          'email' => 'john@example.com',
          'location' => 'San Francisco, California, United States'
        }
      }
    end

    it 'processes all LinkedIn data sections' do
      allow(processor).to receive(:update_basic_fields)
      allow(processor).to receive(:process_avatar)
      allow(processor).to receive(:process_languages)
      allow(processor).to receive(:process_skills)
      allow(processor).to receive(:process_experiences)
      allow(processor).to receive(:process_educations)
      allow(processor).to receive(:generate_curriculum_text)

      result = processor.process_all

      expect(processor).to have_received(:update_basic_fields)
      expect(processor).to have_received(:process_languages)
      expect(processor).to have_received(:process_skills)
      expect(result[:success]).to be true
    end

    it 'returns statistics about processed data' do
      result = processor.process_all

      expect(result).to include(:success, :languages_created, :skills_created)
      expect(result[:success]).to be true
    end
  end

  describe '#update_basic_fields' do
    let(:linkedin_data) do
      {
        'basic_info' => {
          'name' => 'Jane Smith',
          'headline' => 'Senior Developer',
          'summary' => 'Experienced software engineer',
          'location' => 'New York, NY, USA'
        }
      }
    end

    it 'updates candidate basic information' do
      processor.send(:update_basic_fields)

      candidate.reload
      expect(candidate.name).to eq('Jane Smith')
      expect(candidate.role_name).to eq('Senior Developer')
      expect(candidate.self_introduction).to eq('Experienced software engineer')
    end

    it 'parses and sets location' do
      processor.send(:update_basic_fields)

      candidate.reload
      expect(candidate.city).to eq('New York')
      expect(candidate.state).to eq('NY')
      expect(candidate.country).to eq('USA')
    end

    context 'when name is not present' do
      let(:linkedin_data) { { 'basic_info' => {} } }

      it 'does not update name' do
        original_name = candidate.name
        processor.send(:update_basic_fields)

        candidate.reload
        expect(candidate.name).to eq(original_name)
      end
    end
  end

  describe '#parse_location' do
    it 'parses full location with city, state, and country' do
      location = 'San Francisco, California, United States'

      result = processor.send(:parse_location, location)

      expect(result).to eq({
        city: 'San Francisco',
        state: 'California',
        country: 'United States'
      })
    end

    it 'handles location with only city and country' do
      location = 'London, United Kingdom'

      result = processor.send(:parse_location, location)

      expect(result).to eq({
        city: 'London',
        state: nil,
        country: 'United Kingdom'
      })
    end

    it 'handles abbreviated states' do
      location = 'Austin, TX, USA'

      result = processor.send(:parse_location, location)

      expect(result).to eq({
        city: 'Austin',
        state: 'TX',
        country: 'USA'
      })
    end

    it 'returns empty hash for nil location' do
      result = processor.send(:parse_location, nil)

      expect(result).to eq({})
    end
  end

  describe '#process_skills' do
    let(:linkedin_data) do
      {
        'skills' => [ 'Ruby', 'Rails', 'PostgreSQL', 'AWS' ]
      }
    end

    before do
      allow(candidate.skill_relationships).to receive(:exists?).and_return(false)
      allow(candidate.skill_relationships).to receive(:create!)
    end

    it 'creates skills and relationships' do
      result = processor.send(:process_skills)

      expect(result[:created]).to eq(4)
      expect(result[:total]).to eq(4)
    end

    context 'when skill already exists for candidate' do
      before do
        allow(candidate.skill_relationships).to receive(:exists?).and_return(true)
      end

      it 'does not create duplicate relationship' do
        result = processor.send(:process_skills)

        expect(result[:created]).to eq(0)
        expect(result[:total]).to eq(4)
      end
    end

    context 'when no skills in payload' do
      let(:linkedin_data) { {} }

      it 'returns zero skills' do
        result = processor.send(:process_skills)

        expect(result[:created]).to eq(0)
        expect(result[:total]).to eq(0)
      end
    end
  end

  describe '#process_experiences' do
    let(:company) { create(:company, account: account) }
    let(:occupation) { create(:occupation, account: account) }
    let(:linkedin_data) do
      {
        'experience' => [
          {
            'title' => 'Senior Developer',
            'company' => 'Tech Corp',
            'start_date' => { 'year' => 2020, 'month' => 1 },
            'end_date' => { 'year' => 2023, 'month' => 12 },
            'description' => 'Developed web applications'
          }
        ]
      }
    end

    before do
      allow(processor).to receive(:find_or_create_company).and_return(company)
      allow(processor).to receive(:find_or_create_occupation).and_return(occupation)
    end

    it 'creates experience records' do
      expect {
        processor.send(:process_experiences)
      }.to change { candidate.experiences.count }.by(1)
    end

    it 'sets experience dates correctly' do
      processor.send(:process_experiences)

      experience = candidate.experiences.last
      expect(experience.start_date).to eq(Date.new(2020, 1, 1))
      expect(experience.end_date).to eq(Date.new(2023, 12, 31))
    end

    it 'links to company and occupation' do
      processor.send(:process_experiences)

      experience = candidate.experiences.last
      expect(experience.company).to eq(company)
      expect(experience.occupation).to eq(occupation)
    end
  end

  describe '#process_educations' do
    let(:institution) { create(:institution, account: account) }
    let(:study_area) { create(:study_area) }
    let(:linkedin_data) do
      {
        'education' => [
          {
            'school' => 'MIT',
            'degree_name' => "Bachelor's Degree",
            'field_of_study' => 'Computer Science',
            'start_date' => { 'year' => 2015 },
            'end_date' => { 'year' => 2019 }
          }
        ]
      }
    end

    before do
      allow(processor).to receive(:find_or_create_institution).and_return(institution)
      allow(processor).to receive(:find_or_create_study_area).and_return(study_area)
    end

    it 'creates education records' do
      expect {
        processor.send(:process_educations)
      }.to change { candidate.educations.count }.by(1)
    end

    it 'maps degree name to formation type' do
      processor.send(:process_educations)

      education = candidate.educations.last
      expect(education.formation_type).to eq(5)
    end

    it 'links to institution and study area' do
      processor.send(:process_educations)

      education = candidate.educations.last
      expect(education.institution).to eq(institution)
      expect(education.study_area).to eq(study_area)
    end
  end

  describe '#map_formation_type' do
    it 'maps bachelor degree' do
      result = processor.send(:map_formation_type, "Bachelor's Degree")

      expect(result).to eq(5)
    end

    it 'maps master degree to postgraduate' do
      result = processor.send(:map_formation_type, "Master's Degree")

      expect(result).to eq(7)
    end

    it 'maps PhD to postgraduate' do
      result = processor.send(:map_formation_type, 'Doctor of Philosophy')

      expect(result).to eq(7)
    end

    it 'maps high school' do
      result = processor.send(:map_formation_type, 'High School')

      expect(result).to eq(2)
    end

    it 'returns nil for unknown degree' do
      result = processor.send(:map_formation_type, 'Unknown Degree')

      expect(result).to be_nil
    end
  end

  describe '#parse_linkedin_date' do
    it 'parses date with year and month' do
      date_data = { 'year' => 2020, 'month' => 5 }

      result = processor.send(:parse_linkedin_date, date_data)

      expect(result).to eq(Date.new(2020, 5, 1))
    end

    it 'parses date with only year' do
      date_data = { 'year' => 2020 }

      result = processor.send(:parse_linkedin_date, date_data)

      expect(result).to eq(Date.new(2020, 1, 1))
    end

    it 'returns nil for invalid month' do
      date_data = { 'year' => 2020, 'month' => 13 }

      result = processor.send(:parse_linkedin_date, date_data)

      expect(result).to be_nil
    end

    it 'returns nil for nil date data' do
      result = processor.send(:parse_linkedin_date, nil)

      expect(result).to be_nil
    end
  end

  describe '#parse_month_value' do
    it 'parses numeric month string' do
      result = processor.send(:parse_month_value, '5')

      expect(result).to eq(5)
    end

    it 'parses month abbreviation' do
      result = processor.send(:parse_month_value, 'Jan')

      expect(result).to eq(1)
    end

    it 'parses full month name' do
      result = processor.send(:parse_month_value, 'December')

      expect(result).to eq(12)
    end

    it 'returns nil for invalid month' do
      result = processor.send(:parse_month_value, 'InvalidMonth')

      expect(result).to be_nil
    end

    it 'returns value for integer input' do
      result = processor.send(:parse_month_value, 3)

      expect(result).to eq(3)
    end
  end

  describe '#generate_curriculum_text' do
    before do
      allow(Candidates::CurriculumTextGenerator).to receive_message_chain(:new, :generate)
        .and_return('Generated curriculum text')
    end

    it 'generates curriculum text using generator' do
      processor.send(:generate_curriculum_text)

      candidate.reload
      expect(candidate.curriculum_text).to eq('Generated curriculum text')
    end

    it 'uses CurriculumTextGenerator service' do
      expect(Candidates::CurriculumTextGenerator).to receive(:new).with(candidate)

      processor.send(:generate_curriculum_text)
    end
  end
end
