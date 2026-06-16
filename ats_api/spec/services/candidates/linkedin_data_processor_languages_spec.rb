# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Candidates::LinkedinDataProcessor, type: :service do
  let(:account) { Account.new(id: 1) }
  let(:candidate) do
    instance_double(
      Candidate,
      id: 123,
      account: account,
      account_id: 1,
      language_relationships: language_relationships_collection,
      update!: true
    )
  end
  let(:language_relationships_collection) { double('language_relationships', exists?: false, create!: true) }

  let(:linkedin_data) do
    {
      "languages" => [
        {
          "language" => "Portuguese",
          "proficiency" => "Native or bilingual proficiency"
        },
        {
          "language" => "English",
          "proficiency" => "Professional working proficiency"
        },
        {
          "language" => "Spanish",
          "proficiency" => "Elementary proficiency"
        }
      ],
      "basic_info" => {}
    }
  end

  let(:processor) { described_class.new(candidate, linkedin_data) }

  describe '#process_languages' do
    context 'when there are languages in payload' do
      let(:portuguese) { instance_double(Language, id: 1, name: 'Portuguese') }
      let(:english) { instance_double(Language, id: 2, name: 'English') }
      let(:spanish) { instance_double(Language, id: 3, name: 'Spanish') }

      before do
        allow(Language).to receive(:where).with("LOWER(name) = ? OR LOWER(name_ptbr) = ?", 'portuguese', 'portuguese').and_return([ portuguese ])
        allow(Language).to receive(:where).with("LOWER(name) = ? OR LOWER(name_ptbr) = ?", 'english', 'english').and_return([ english ])
        allow(Language).to receive(:where).with("LOWER(name) = ? OR LOWER(name_ptbr) = ?", 'spanish', 'spanish').and_return([ spanish ])

        allow(language_relationships_collection).to receive(:exists?).with(language_id: 1).and_return(false)
        allow(language_relationships_collection).to receive(:exists?).with(language_id: 2).and_return(false)
        allow(language_relationships_collection).to receive(:exists?).with(language_id: 3).and_return(false)
      end

      it 'processes all languages' do
        result = processor.send(:process_languages)

        expect(result[:created]).to eq(3)
        expect(result[:total]).to eq(3)
      end

      it 'creates relationships with correct levels' do
        expect(language_relationships_collection).to receive(:create!).with(
          language_id: 1,
          level: 'nativo',
          reference_type: 'Candidate',
          reference_id: 123
        )

        expect(language_relationships_collection).to receive(:create!).with(
          language_id: 2,
          level: 'avançado',
          reference_type: 'Candidate',
          reference_id: 123
        )

        expect(language_relationships_collection).to receive(:create!).with(
          language_id: 3,
          level: 'básico',
          reference_type: 'Candidate',
          reference_id: 123
        )

        processor.send(:process_languages)
      end
    end

    context 'when there are no languages in payload' do
      let(:linkedin_data) { { "basic_info" => {} } }

      it 'returns zero languages created' do
        result = processor.send(:process_languages)

        expect(result[:created]).to eq(0)
      end
    end

    context 'when language is already linked' do
      let(:portuguese) { instance_double(Language, id: 1, name: 'Portuguese') }

      before do
        allow(Language).to receive(:where).and_return([ portuguese ])
        allow(language_relationships_collection).to receive(:exists?).with(language_id: 1).and_return(true)
      end

      it 'does not create duplicate relationship' do
        expect(language_relationships_collection).not_to receive(:create!)

        result = processor.send(:process_languages)
        expect(result[:created]).to eq(0)
        expect(result[:total]).to eq(3)
      end
    end
  end

  describe '#map_proficiency_to_level' do
    it 'maps "Native or bilingual proficiency" to nativo' do
      level = processor.send(:map_proficiency_to_level, 'Native or bilingual proficiency')
      expect(level).to eq('nativo')
    end

    it 'maps "Full professional proficiency" to fluente' do
      level = processor.send(:map_proficiency_to_level, 'Full professional proficiency')
      expect(level).to eq('fluente')
    end

    it 'maps "Professional working proficiency" to avançado' do
      level = processor.send(:map_proficiency_to_level, 'Professional working proficiency')
      expect(level).to eq('avançado')
    end

    it 'maps "Limited working proficiency" to intermediário' do
      level = processor.send(:map_proficiency_to_level, 'Limited working proficiency')
      expect(level).to eq('intermediário')
    end

    it 'maps "Elementary proficiency" to básico' do
      level = processor.send(:map_proficiency_to_level, 'Elementary proficiency')
      expect(level).to eq('básico')
    end

    it 'returns intermediário as default for unknown proficiency' do
      level = processor.send(:map_proficiency_to_level, 'Unknown level')
      expect(level).to eq('intermediário')
    end

    it 'returns nil when proficiency is blank' do
      level = processor.send(:map_proficiency_to_level, nil)
      expect(level).to be_nil
    end
  end

  describe '#normalize_language_name' do
    it 'normalizes common language names' do
      expect(processor.send(:normalize_language_name, 'english')).to eq('English')
      expect(processor.send(:normalize_language_name, 'portuguese')).to eq('Portuguese')
      expect(processor.send(:normalize_language_name, 'spanish')).to eq('Spanish')
    end

    it 'capitalizes unmapped languages' do
      expect(processor.send(:normalize_language_name, 'greek')).to eq('Greek')
    end

    it 'converts Mandarin to Chinese' do
      expect(processor.send(:normalize_language_name, 'mandarin')).to eq('Chinese')
    end
  end

  describe '#generate_language_acronym' do
    it 'generates acronyms for known languages' do
      expect(processor.send(:generate_language_acronym, 'English')).to eq('EN')
      expect(processor.send(:generate_language_acronym, 'Portuguese')).to eq('PT')
      expect(processor.send(:generate_language_acronym, 'Spanish')).to eq('ES')
    end

    it 'generates 2-letter acronym for unknown languages' do
      expect(processor.send(:generate_language_acronym, 'Greek')).to eq('GR')
    end
  end

  describe '#translate_language_to_portuguese' do
    it 'translates language names to portuguese' do
      expect(processor.send(:translate_language_to_portuguese, 'English')).to eq('Inglês')
      expect(processor.send(:translate_language_to_portuguese, 'Portuguese')).to eq('Português')
      expect(processor.send(:translate_language_to_portuguese, 'Spanish')).to eq('Espanhol')
    end

    it 'returns original name if no translation available' do
      expect(processor.send(:translate_language_to_portuguese, 'Greek')).to eq('Greek')
    end
  end
end
