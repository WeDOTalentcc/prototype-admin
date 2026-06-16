require "rails_helper"

RSpec.describe Apify::LinkedinSearchService::Profile do
  describe "validacao de campos obrigatorios (G-06)" do
    context "com todos os campos obrigatorios presentes" do
      let(:valid_data) do
        {
          "publicIdentifier" => "joao-silva",
          "linkedinUrl" => "https://linkedin.com/in/joao-silva",
          "firstName" => "Joao",
          "lastName" => "Silva"
        }
      end

      it "inicializa sem erro" do
        expect { described_class.new(valid_data) }.not_to raise_error
      end

      it "valid? retorna true" do
        expect(described_class.new(valid_data).valid?).to be true
      end
    end

    context "sem publicIdentifier" do
      let(:data) { { "linkedinUrl" => "https://linkedin.com/in/x" } }

      it "raise ParseError com nome do campo ausente" do
        expect { described_class.new(data) }
          .to raise_error(Apify::LinkedinSearchService::Profile::ParseError, /public_identifier/)
      end
    end

    context "sem linkedinUrl" do
      let(:data) { { "publicIdentifier" => "joao-silva" } }

      it "raise ParseError com nome do campo ausente" do
        expect { described_class.new(data) }
          .to raise_error(Apify::LinkedinSearchService::Profile::ParseError, /linkedin_url/)
      end
    end

    context "com ambos os campos ausentes" do
      it "raise ParseError listando os dois campos" do
        expect { described_class.new({}) }
          .to raise_error(Apify::LinkedinSearchService::Profile::ParseError, /public_identifier.*linkedin_url|linkedin_url.*public_identifier/)
      end
    end

    context "com campos presentes mas vazios" do
      let(:data) { { "publicIdentifier" => "", "linkedinUrl" => "" } }

      it "raise ParseError — string vazia nao conta como presente" do
        expect { described_class.new(data) }
          .to raise_error(Apify::LinkedinSearchService::Profile::ParseError)
      end
    end
  end
end
