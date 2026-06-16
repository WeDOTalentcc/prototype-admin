# frozen_string_literal: true

require 'rails_helper'

RSpec.describe CandidateService::TextBuilder do
  describe '.call' do
    let(:candidate) do
      instance_double(
        Candidate,
        name: 'John Doe',
        role_name: 'Senior Developer',
        position_level: 'Senior',
        current_company: 'Tech Corp',
        city: 'San Francisco',
        state: 'CA',
        country: 'USA',
        curriculum_text: 'Professional summary...',
        self_introduction: 'Experienced software engineer',
        interests: 'AI, Machine Learning',
        remote_work: true,
        mobility: false,
        current_salary: 10000,
        desired_salary: 15000,
        currency: 'USD',
        source: 'LinkedIn'
      )
    end

    before do
      allow(candidate).to receive(:respond_to?).with(:skills).and_return(false)
      allow(candidate).to receive(:respond_to?).with(:experiences).and_return(false)
      allow(candidate).to receive(:respond_to?).with(:educations).and_return(false)
      allow(candidate).to receive(:respond_to?).with(:language_relationships).and_return(false)
    end

    it 'generates text representation of candidate' do
      result = described_class.call(candidate)

      expect(result).to include('John Doe')
      expect(result).to include('Senior Developer')
      expect(result).to include('Tech Corp')
    end

    it 'includes curriculum text' do
      result = described_class.call(candidate)

      expect(result).to include('Resume:')
      expect(result).to include('Professional summary')
    end

    it 'includes metadata' do
      result = described_class.call(candidate)

      expect(result).to include('remote: yes')
      expect(result).to include('mobility: no')
      expect(result).to include('interests: AI, Machine Learning')
    end

    context 'when candidate has skills' do
      let(:skills) { [ double(name: 'Ruby'), double(name: 'Rails'), double(name: 'PostgreSQL') ] }

      before do
        allow(candidate).to receive(:respond_to?).with(:skills).and_return(true)
        allow(candidate).to receive(:skills).and_return(skills)
      end

      it 'includes skills section' do
        result = described_class.call(candidate)

        expect(result).to include('Skills:')
        expect(result).to include('Ruby')
        expect(result).to include('Rails')
        expect(result).to include('PostgreSQL')
      end
    end

    context 'when candidate has experiences' do
      let(:occupation) { double(name: 'Software Engineer') }
      let(:company) { double(name: 'Tech Inc') }
      let(:experience) do
        double(
          occupation: occupation,
          company: company,
          start_date: Date.new(2020, 1, 1),
          end_date: Date.new(2023, 12, 31),
          work_here: false,
          contract_type: 'CLT',
          description: 'Developed web applications'
        )
      end
      let(:experiences) { [ experience ] }

      before do
        allow(candidate).to receive(:respond_to?).with(:experiences).and_return(true)
        allow(candidate).to receive(:experiences).and_return(experiences)
        allow(experiences).to receive(:order).and_return(experiences)
        allow(experiences).to receive(:limit).and_return(experiences)
      end

      it 'includes experience section' do
        result = described_class.call(candidate)

        expect(result).to include('Experience:')
        expect(result).to include('Software Engineer')
        expect(result).to include('Tech Inc')
        expect(result).to include('CLT')
      end
    end

    context 'when candidate has educations' do
      let(:institution) { double(name: 'MIT') }
      let(:study_area) { double(name: 'Computer Science') }
      let(:education) do
        double(
          institution: institution,
          study_area: study_area,
          formation_type: 5,
          start_date: Date.new(2015, 1, 1),
          end_date: Date.new(2019, 12, 31)
        )
      end
      let(:educations) { [ education ] }

      before do
        allow(candidate).to receive(:respond_to?).with(:educations).and_return(true)
        allow(candidate).to receive(:educations).and_return(educations)
        allow(educations).to receive(:order).and_return(educations)
        allow(educations).to receive(:limit).and_return(educations)
      end

      it 'includes education section' do
        result = described_class.call(candidate)

        expect(result).to include('Education:')
        expect(result).to include("Bachelor's")
        expect(result).to include('Computer Science')
        expect(result).to include('MIT')
      end
    end

    context 'when candidate has languages' do
      let(:language) { double(name: 'English') }
      let(:language_relationship) { double(language: language, level: 'Fluent') }
      let(:language_relationships) { [ language_relationship ] }

      before do
        allow(candidate).to receive(:respond_to?).with(:language_relationships).and_return(true)
        allow(candidate).to receive(:language_relationships).and_return(language_relationships)
      end

      it 'includes languages section' do
        result = described_class.call(candidate)

        expect(result).to include('Languages:')
        expect(result).to include('English (Fluent)')
      end
    end
  end

  describe '.build_header' do
    let(:candidate) do
      instance_double(
        Candidate,
        name: 'Jane Smith',
        role_name: 'Product Manager',
        position_level: 'Senior',
        current_company: 'StartupXYZ',
        city: 'Austin',
        state: 'TX',
        country: 'USA'
      )
    end

    before do
      allow(candidate).to receive(:respond_to?).with(:experiences).and_return(false)
      allow(described_class).to receive(:calculate_total_experience).and_return(8)
    end

    it 'builds complete header' do
      result = described_class.send(:build_header, candidate)

      expect(result).to include('Jane Smith')
      expect(result).to include('Product Manager')
      expect(result).to include('Senior')
      expect(result).to include('StartupXYZ')
      expect(result).to include('Austin, TX, USA')
      expect(result).to include('8 years of experience')
    end
  end

  describe '.calculate_total_experience' do
    let(:candidate) { double }
    let(:experiences) do
      [
        double(
          start_date: Date.new(2015, 1, 1),
          end_date: Date.new(2017, 12, 31),
          work_here: false
        ),
        double(
          start_date: Date.new(2018, 1, 1),
          end_date: nil,
          work_here: true
        )
      ]
    end

    before do
      allow(candidate).to receive(:respond_to?).with(:experiences).and_return(true)
      allow(candidate).to receive(:experiences).and_return(experiences)
    end

    it 'calculates total years from all experiences' do
      result = described_class.send(:calculate_total_experience, candidate)

      expect(result).to be > 0
    end

    it 'includes current job in calculation' do
      travel_to(Date.new(2023, 1, 1)) do
        result = described_class.send(:calculate_total_experience, candidate)

        expect(result).to be >= 8
      end
    end

    context 'when candidate has no experiences' do
      before do
        allow(candidate).to receive(:respond_to?).with(:experiences).and_return(false)
      end

      it 'returns zero' do
        result = described_class.send(:calculate_total_experience, candidate)

        expect(result).to eq(0)
      end
    end
  end

  describe '.format_duration' do
    it 'formats duration with start and end year' do
      start_date = Date.new(2020, 1, 1)
      end_date = Date.new(2023, 12, 31)

      result = described_class.send(:format_duration, start_date, end_date, false)

      expect(result).to eq('2020-2023')
    end

    it 'shows present for current positions' do
      start_date = Date.new(2020, 1, 1)

      result = described_class.send(:format_duration, start_date, nil, true)

      expect(result).to eq('2020-present')
    end

    it 'returns empty string when no start date' do
      result = described_class.send(:format_duration, nil, nil, false)

      expect(result).to eq('')
    end
  end

  describe '.format_education_level' do
    it 'formats bachelor degree' do
      result = described_class.send(:format_education_level, 5)

      expect(result).to eq("Bachelor's")
    end

    it 'formats postgraduate' do
      result = described_class.send(:format_education_level, 7)

      expect(result).to eq('Postgraduate')
    end

    it 'formats PhD' do
      result = described_class.send(:format_education_level, 9)

      expect(result).to eq('PhD')
    end

    it 'returns nil for unknown type' do
      result = described_class.send(:format_education_level, 99)

      expect(result).to be_nil
    end
  end

  describe '.assemble_with_truncation' do
    it 'assembles sections in priority order' do
      sections = [
        { priority: 3, content: 'Low priority' },
        { priority: 1, content: 'High priority' },
        { priority: 2, content: 'Medium priority' }
      ]

      result = described_class.send(:assemble_with_truncation, sections)

      expect(result).to start_with('High priority')
      expect(result).to include('Medium priority')
      expect(result).to include('Low priority')
    end

    it 'truncates when exceeding MAX_CHARS' do
      long_content = 'A' * (described_class::MAX_CHARS + 1000)
      sections = [
        { priority: 1, content: long_content }
      ]

      result = described_class.send(:assemble_with_truncation, sections)

      expect(result.length).to be <= described_class::MAX_CHARS + 50
    end

    it 'skips empty sections' do
      sections = [
        { priority: 1, content: 'Content' },
        { priority: 2, content: '' },
        { priority: 3, content: nil }
      ]

      result = described_class.send(:assemble_with_truncation, sections)

      expect(result).to eq('Content')
    end
  end
end
