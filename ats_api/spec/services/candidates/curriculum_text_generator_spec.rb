# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::CurriculumTextGenerator do
  subject(:generator) { described_class.new(candidate) }

  let(:candidate) do
    instance_double(
      Candidate,
      name: 'John Doe',
      email: 'john@example.com',
      mobile_phone: '+1234567890',
      linkedin: 'linkedin.com/in/johndoe',
      role_name: 'Senior Developer',
      current_company: 'Tech Corp',
      city: 'San Francisco',
      state: 'CA',
      country: 'USA',
      self_introduction: 'Experienced software engineer',
      remote_work: true,
      mobility: false,
      interests: 'AI, Machine Learning',
      github: 'github.com/johndoe',
      portfolio: 'johndoe.dev',
      skills: [],
      languages: [],
      language_relationships: []
    )
  end

  describe '#generate' do
    context 'when candidate has complete information' do
      let(:skills) { double('skills', pluck: [ 'Ruby', 'Rails', 'PostgreSQL' ]) }
      let(:languages) { double('languages', empty?: false) }
      let(:experiences) { double('experiences') }
      let(:educations) { double('educations') }

      before do
        allow(candidate).to receive(:skills).and_return(skills)
        allow(candidate).to receive(:languages).and_return(languages)
        allow(languages).to receive(:includes).and_return([])
        allow(candidate).to receive(:experiences).and_return(experiences)
        allow(experiences).to receive(:includes).and_return(experiences)
        allow(experiences).to receive(:order).and_return([])
        allow(candidate).to receive(:educations).and_return(educations)
        allow(educations).to receive(:includes).and_return(educations)
        allow(educations).to receive(:order).and_return([])
      end

      it 'generates formatted curriculum text' do
        result = generator.generate

        expect(result).to include('JOHN DOE')
        expect(result).to include('john@example.com')
        expect(result).to include('Senior Developer at Tech Corp')
        expect(result).to include('San Francisco, CA, USA')
      end

      it 'includes about section' do
        result = generator.generate

        expect(result).to include('ABOUT')
        expect(result).to include('Experienced software engineer')
      end

      it 'includes skills section' do
        result = generator.generate

        expect(result).to include('SKILLS')
        expect(result).to include('Ruby, Rails, PostgreSQL')
      end

      it 'includes additional information' do
        result = generator.generate

        expect(result).to include('ADDITIONAL INFORMATION')
        expect(result).to include('Remote Work: Yes')
        expect(result).to include('Interests: AI, Machine Learning')
        expect(result).to include('GitHub: github.com/johndoe')
      end
    end

    context 'when candidate has minimal information' do
      let(:minimal_candidate) do
        instance_double(
          Candidate,
          name: 'Jane Smith',
          email: nil,
          mobile_phone: nil,
          linkedin: nil,
          role_name: nil,
          current_company: nil,
          city: nil,
          state: nil,
          country: nil,
          self_introduction: nil,
          remote_work: nil,
          mobility: nil,
          interests: nil,
          github: nil,
          portfolio: nil,
          skills: double(pluck: []),
          languages: double(empty?: true, includes: []),
          language_relationships: [],
          experiences: double(includes: double(order: [])),
          educations: double(includes: double(order: []))
        )
      end

      subject(:generator) { described_class.new(minimal_candidate) }

      it 'generates only name when minimal data' do
        result = generator.generate

        expect(result).to include('JANE SMITH')
        expect(result).not_to include('ABOUT')
        expect(result).not_to include('SKILLS')
        expect(result).not_to include('ADDITIONAL INFORMATION')
      end
    end

    context 'when experiences exist' do
      let(:experience) do
        double(
          occupation: double(name: 'Software Engineer'),
          company: double(name: 'Tech Corp'),
          start_date: Date.new(2020, 1, 1),
          end_date: Date.new(2022, 12, 31),
          work_here: false,
          description: 'Developed web applications'
        )
      end

      let(:experiences) { double('experiences') }

      before do
        allow(candidate).to receive(:skills).and_return(double(pluck: []))
        allow(candidate).to receive(:languages).and_return(double(empty?: true, includes: []))
        allow(candidate).to receive(:experiences).and_return(experiences)
        allow(experiences).to receive(:includes).and_return(experiences)
        allow(experiences).to receive(:order).and_return([ experience ])
        allow(candidate).to receive(:educations).and_return(double(includes: double(order: [])))
      end

      it 'formats experience correctly' do
        result = generator.generate

        expect(result).to include('PROFESSIONAL EXPERIENCE')
        expect(result).to include('Software Engineer at Tech Corp')
        expect(result).to include('Jan 2020 - Dec 2022')
        expect(result).to include('Developed web applications')
      end
    end

    context 'when education exists' do
      let(:education) do
        double(
          institution: double(name: 'State University'),
          study_area: double(name: 'Computer Science'),
          formation_type: 5,
          start_date: Date.new(2015, 9, 1),
          end_date: Date.new(2019, 5, 31),
          study_here: false
        )
      end

      let(:educations) { double('educations') }

      before do
        allow(candidate).to receive(:skills).and_return(double(pluck: []))
        allow(candidate).to receive(:languages).and_return(double(empty?: true, includes: []))
        allow(candidate).to receive(:experiences).and_return(double(includes: double(order: [])))
        allow(candidate).to receive(:educations).and_return(educations)
        allow(educations).to receive(:includes).and_return(educations)
        allow(educations).to receive(:order).and_return([ education ])
      end

      it 'formats education correctly' do
        result = generator.generate

        expect(result).to include('EDUCATION')
        expect(result).to include("Bachelor's Degree in Computer Science - State University")
        expect(result).to include('Sep 2015 - May 2019')
      end
    end

    context 'when languages exist' do
      let(:language) { double(id: 1, name: 'English') }
      let(:language_relationship) { double(language_id: 1, proficiency: 'Fluent') }
      let(:languages) { [ language ] }

      before do
        allow(candidate).to receive(:skills).and_return(double(pluck: []))
        allow(candidate).to receive(:languages).and_return(languages)
        allow(languages).to receive(:includes).with(:language_relationships).and_return(languages)
        allow(candidate).to receive(:language_relationships).and_return([ language_relationship ])
        allow(candidate.language_relationships).to receive(:find_by).with(language_id: 1).and_return(language_relationship)
        allow(candidate).to receive(:experiences).and_return(double(includes: double(order: [])))
        allow(candidate).to receive(:educations).and_return(double(includes: double(order: [])))
      end

      it 'formats languages with proficiency' do
        result = generator.generate

        expect(result).to include('LANGUAGES')
        expect(result).to include('English (Fluent)')
      end
    end
  end

  describe '#build_date_range' do
    it 'formats date range correctly' do
      start_date = Date.new(2020, 1, 15)
      end_date = Date.new(2022, 12, 31)

      result = generator.send(:build_date_range, start_date, end_date, false)

      expect(result).to eq('Jan 2020 - Dec 2022')
    end

    it 'shows Present for current positions' do
      start_date = Date.new(2020, 1, 15)

      result = generator.send(:build_date_range, start_date, nil, true)

      expect(result).to eq('Jan 2020 - Present')
    end

    it 'handles only start date' do
      start_date = Date.new(2020, 1, 15)

      result = generator.send(:build_date_range, start_date, nil, false)

      expect(result).to eq('Jan 2020')
    end

    it 'returns nil when no start date' do
      result = generator.send(:build_date_range, nil, nil, false)

      expect(result).to be_nil
    end
  end

  describe '#map_formation_type_name' do
    it 'maps formation types correctly' do
      expect(generator.send(:map_formation_type_name, 1)).to eq('Elementary School')
      expect(generator.send(:map_formation_type_name, 5)).to eq("Bachelor's Degree")
      expect(generator.send(:map_formation_type_name, 7)).to eq('Postgraduate')
    end

    it 'returns Other for unknown types' do
      expect(generator.send(:map_formation_type_name, 99)).to eq('Other')
      expect(generator.send(:map_formation_type_name, nil)).to eq('Other')
    end
  end

  describe '#safe_attribute' do
    it 'safely accesses nested attributes' do
      obj = double(company: double(name: 'Tech Corp'))

      result = generator.send(:safe_attribute, obj, :company, :name)

      expect(result).to eq('Tech Corp')
    end

    it 'returns nil when attribute does not exist' do
      obj = double(company: nil)

      result = generator.send(:safe_attribute, obj, :company, :name)

      expect(result).to be_nil
    end

    it 'returns nil when object is nil' do
      result = generator.send(:safe_attribute, nil, :company, :name)

      expect(result).to be_nil
    end

    it 'handles exceptions gracefully' do
      obj = double
      allow(obj).to receive(:company).and_raise(StandardError)

      result = generator.send(:safe_attribute, obj, :company, :name)

      expect(result).to be_nil
    end
  end
end
