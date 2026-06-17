# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Pearch::SearchProfilesBuilder, '#reveal_emails and #reveal_phones' do
  describe '.build com reveal_emails flag' do
    context 'quando reveal_emails: true' do
      let(:params) { { reveal_emails: true, type: 'fast' } }

      it 'adiciona reveal_emails: true' do
        result = described_class.build(params)

        expect(result[:reveal_emails]).to be true
      end

      it 'mantém outras configurações' do
        result = described_class.build(params)

        expect(result[:type]).to eq('fast')
        expect(result[:filter_out_no_emails]).to be false
        expect(result[:reveal_phones]).to be false
      end
    end

    context 'quando reveal_emails: false' do
      let(:params) { { reveal_emails: false, type: 'fast' } }

      it 'define reveal_emails: false' do
        result = described_class.build(params)

        expect(result[:reveal_emails]).to be false
      end
    end

    context 'quando reveal_emails não está presente' do
      let(:params) { { type: 'fast' } }

      it 'usa reveal_emails default (false)' do
        result = described_class.build(params)

        expect(result[:reveal_emails]).to be false
      end
    end

    context 'backward compatibility: show_emails' do
      let(:params) { { show_emails: true, type: 'fast' } }

      it 'mapeia show_emails para reveal_emails (nomenclatura antiga)' do
        result = described_class.build(params)

        expect(result[:reveal_emails]).to be true
      end
    end

    context 'precedência: reveal_emails sobre show_emails' do
      let(:params) { { reveal_emails: true, show_emails: false, type: 'fast' } }

      it 'reveal_emails tem precedência sobre show_emails' do
        result = described_class.build(params)

        expect(result[:reveal_emails]).to be true
      end
    end
  end

  describe '.build com reveal_phones flag' do
    context 'quando reveal_phones: true' do
      let(:params) { { reveal_phones: true, type: 'fast' } }

      it 'adiciona reveal_phones: true' do
        result = described_class.build(params)

        expect(result[:reveal_phones]).to be true
      end

      it 'mantém outras configurações' do
        result = described_class.build(params)

        expect(result[:type]).to eq('fast')
        expect(result[:filter_out_no_phones]).to be false
        expect(result[:reveal_emails]).to be false
      end
    end

    context 'quando reveal_phones: false' do
      let(:params) { { reveal_phones: false, type: 'fast' } }

      it 'define reveal_phones: false' do
        result = described_class.build(params)

        expect(result[:reveal_phones]).to be false
      end
    end

    context 'quando reveal_phones não está presente' do
      let(:params) { { type: 'fast' } }

      it 'usa reveal_phones default (false)' do
        result = described_class.build(params)

        expect(result[:reveal_phones]).to be false
      end
    end

    context 'backward compatibility: show_phone_numbers' do
      let(:params) { { show_phone_numbers: true, type: 'fast' } }

      it 'mapeia show_phone_numbers para reveal_phones (nomenclatura antiga)' do
        result = described_class.build(params)

        expect(result[:reveal_phones]).to be true
      end
    end

    context 'precedência: reveal_phones sobre show_phone_numbers' do
      let(:params) { { reveal_phones: true, show_phone_numbers: false, type: 'fast' } }

      it 'reveal_phones tem precedência sobre show_phone_numbers' do
        result = described_class.build(params)

        expect(result[:reveal_phones]).to be true
      end
    end
  end

  describe 'combinação de reveal_emails e reveal_phones' do
    context 'quando ambos são true' do
      let(:params) { { reveal_emails: true, reveal_phones: true, type: 'fast' } }

      it 'aplica ambos os parâmetros' do
        result = described_class.build(params)

        expect(result[:reveal_emails]).to be true
        expect(result[:reveal_phones]).to be true
      end
    end

    context 'combinado com filters' do
      let(:params) do
        {
          filter_out_no_emails: true,
          reveal_emails: true,
          filter_out_no_phones: true,
          reveal_phones: true,
          type: 'fast'
        }
      end

      it 'aplica filters e reveals simultaneamente' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
        expect(result[:reveal_emails]).to be true
        expect(result[:filter_out_no_phones]).to be true
        expect(result[:reveal_phones]).to be true
      end
    end

    context 'reveal sem filter (não recomendado mas válido)' do
      let(:params) { { reveal_emails: true, type: 'fast' } }

      it 'permite reveal_emails sem filter_out_no_emails' do
        result = described_class.build(params)

        expect(result[:reveal_emails]).to be true
        expect(result[:filter_out_no_emails]).to be false
      end
    end
  end

  describe 'combinação com has_* flags' do
    context 'has_email + reveal_emails (uso comum)' do
      let(:params) { { has_email: true, reveal_emails: true, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'aplica ambos: filter + reveal' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
        expect(result[:reveal_emails]).to be true
      end
    end

    context 'has_phone + reveal_phones (uso comum)' do
      let(:params) { { has_phone: true, reveal_phones: true, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'aplica ambos: filter + reveal' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones]).to be true
        expect(result[:reveal_phones]).to be true
      end
    end
  end
end
