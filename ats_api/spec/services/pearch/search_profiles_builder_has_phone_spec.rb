# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Pearch::SearchProfilesBuilder, '#has_phone and #has_email_or_phone' do
  describe '.build com has_phone flag' do
    context 'quando has_phone: true' do
      let(:params) { { has_phone: true, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'adiciona filter_out_no_phones: true' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones]).to be true
      end

      it 'loga que está aplicando filter_out_no_phones' do
        expect(Rails.logger).to receive(:info).with(/has_phone=true detectado/)

        described_class.build(params)
      end

      it 'mantém outras configurações' do
        result = described_class.build(params)

        expect(result[:type]).to eq('fast')
        expect(result[:filter_out_no_emails]).to be false
      end
    end

    context 'quando has_phone: false' do
      let(:params) { { has_phone: false, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'não adiciona filter_out_no_phones' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones]).to be false
      end
    end

    context 'quando has_phone não está presente' do
      let(:params) { { type: 'fast' } }

      it 'usa filter_out_no_phones default (false)' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones]).to be false
      end
    end
  end

  describe '.build com has_email_or_phone flag' do
    context 'quando has_email_or_phone: true' do
      let(:params) { { has_email_or_phone: true, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'adiciona filter_out_no_phones_or_emails: true' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones_or_emails]).to be true
      end

      it 'loga que está aplicando filter_out_no_phones_or_emails' do
        expect(Rails.logger).to receive(:info).with(/has_email_or_phone=true detectado/)

        described_class.build(params)
      end

      it 'mantém outras configurações' do
        result = described_class.build(params)

        expect(result[:type]).to eq('fast')
        expect(result[:filter_out_no_emails]).to be false
        expect(result[:filter_out_no_phones]).to be false
      end
    end

    context 'quando has_email_or_phone: "true" (string)' do
      let(:params) { { has_email_or_phone: "true", type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'converte e adiciona filter_out_no_phones_or_emails: true' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones_or_emails]).to be true
      end
    end

    context 'quando has_email_or_phone: false' do
      let(:params) { { has_email_or_phone: false, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'não adiciona filter_out_no_phones_or_emails' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones_or_emails]).to be false
      end
    end
  end

  describe 'precedência de filtros' do
    context 'quando has_phone: true e require_phone_numbers: false' do
      let(:params) { { has_phone: true, require_phone_numbers: false, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'has_phone tem precedência sobre require_phone_numbers (backward compatibility)' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones]).to be true
      end
    end

    context 'quando has_email_or_phone: true e require_phones_or_emails: false' do
      let(:params) { { has_email_or_phone: true, require_phones_or_emails: false, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'has_email_or_phone tem precedência sobre require_phones_or_emails (backward compatibility)' do
        result = described_class.build(params)

        expect(result[:filter_out_no_phones_or_emails]).to be true
      end
    end
  end

  describe 'combinação de filtros' do
    context 'quando has_email: true e has_phone: true' do
      let(:params) { { has_email: true, has_phone: true, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'aplica ambos os filtros' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
        expect(result[:filter_out_no_phones]).to be true
      end
    end

    context 'quando has_email: true e has_email_or_phone: true' do
      let(:params) { { has_email: true, has_email_or_phone: true, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'aplica ambos os filtros' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
        expect(result[:filter_out_no_phones_or_emails]).to be true
      end
    end
  end
end
