# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Pearch::SearchProfilesBuilder, '#has_email' do
  describe '.build com has_email flag' do
    context 'quando has_email: true' do
      let(:params) { { has_email: true, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'adiciona filter_out_no_emails: true' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
      end

      it 'loga que está aplicando filter_out_no_emails' do
        expect(Rails.logger).to receive(:info).with(/has_email=true detectado/)

        described_class.build(params)
      end

      it 'mantém outras configurações' do
        result = described_class.build(params)

        expect(result[:type]).to eq('fast')
        expect(result[:reveal_emails]).to be false
        expect(result[:filter_out_no_phones]).to be false
      end
    end

    context 'quando has_email: "true" (string)' do
      let(:params) { { has_email: "true", type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'converte e adiciona filter_out_no_emails: true' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
      end
    end

    context 'quando has_email: false' do
      let(:params) { { has_email: false, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'não adiciona filter_out_no_emails' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be false
      end

      it 'não loga sobre has_email' do
        expect(Rails.logger).not_to receive(:info).with(/has_email=true/)

        described_class.build(params)
      end
    end

    context 'quando has_email não está presente' do
      let(:params) { { type: 'fast' } }

      it 'usa filter_out_no_emails default (false)' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be false
      end
    end

    context 'quando has_email: true e require_emails: false (backward compatibility)' do
      let(:params) { { has_email: true, require_emails: false, type: 'fast' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'has_email tem precedência sobre require_emails (nomenclatura antiga)' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
      end
    end

    context 'com search_profile balanced' do
      let(:params) { { has_email: true, search_profile: 'balanced' } }

      before do
        allow(Rails.logger).to receive(:info)
      end

      it 'adiciona filter_out_no_emails ao profile balanced' do
        result = described_class.build(params)

        expect(result[:filter_out_no_emails]).to be true
        expect(result[:type]).to eq('fast')
        expect(result[:limit]).to eq(20)
      end
    end
  end
end
