# frozen_string_literal: true

require 'rails_helper'

RSpec.describe LinkedinUrlValidator do
  describe '.valid?' do
    context 'with valid URLs' do
      it 'accepts full linkedin URL with https' do
        expect(described_class.valid?("https://www.linkedin.com/in/john-doe")).to be true
      end

      it 'accepts full linkedin URL with http' do
        expect(described_class.valid?("http://linkedin.com/in/jane-smith")).to be true
      end

      it 'accepts linkedin URL without protocol' do
        expect(described_class.valid?("linkedin.com/in/john-doe")).to be true
      end

      it 'accepts linkedin URL without www' do
        expect(described_class.valid?("https://linkedin.com/in/john-doe")).to be true
      end

      it 'accepts just username' do
        expect(described_class.valid?("john-doe")).to be true
      end

      it 'accepts username with underscores' do
        expect(described_class.valid?("john_doe_123")).to be true
      end
    end

    context 'with invalid URLs' do
      it 'rejects empty string' do
        expect(described_class.valid?("")).to be false
      end

      it 'rejects nil' do
        expect(described_class.valid?(nil)).to be false
      end

      it 'rejects non-linkedin URLs' do
        expect(described_class.valid?("https://facebook.com/john")).to be false
      end

      it 'rejects URLs with special characters' do
        expect(described_class.valid?("john@doe")).to be false
      end

      it 'rejects URLs without /in/ path' do
        expect(described_class.valid?("https://linkedin.com/company/tech")).to be false
      end
    end
  end
end
