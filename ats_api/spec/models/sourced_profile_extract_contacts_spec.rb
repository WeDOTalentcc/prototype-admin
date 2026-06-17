# frozen_string_literal: true

require "rails_helper"

RSpec.describe SourcedProfile, type: :model do
  let(:account) { create(:account) }

  describe "#extract_contacts_from_arrays" do
    context "quando emails é array de strings (formato Pearch)" do
      it "extrai o primeiro email corretamente" do
        profile = SourcedProfile.new(
          account: account,
          uid: SecureRandom.uuid,
          provider: "test",
          emails: [ "john@company.com", "john@personal.com" ],
          email: nil
        )

        profile.send(:extract_contacts_from_arrays)

        expect(profile.email).to eq("john@company.com")
        expect(profile.secondary_email).to eq("john@personal.com")
      end

      it "não sobrescreve email existente" do
        profile = SourcedProfile.new(
          account: account,
          uid: SecureRandom.uuid,
          provider: "test",
          emails: [ "new@company.com", "new@personal.com" ],
          email: "existing@company.com"
        )

        profile.send(:extract_contacts_from_arrays)

        expect(profile.email).to eq("existing@company.com")
      end
    end

    context "quando emails é array de hashes (formato antigo)" do
      it "extrai o primeiro email do hash corretamente" do
        profile = SourcedProfile.new(
          account: account,
          uid: SecureRandom.uuid,
          provider: "test",
          emails: [ { "email" => "john@company.com" }, { "email" => "john@personal.com" } ],
          email: nil
        )

        profile.send(:extract_contacts_from_arrays)

        expect(profile.email).to eq("john@company.com")
        expect(profile.secondary_email).to eq("john@personal.com")
      end
    end

    context "quando emails está vazio" do
      it "não define email" do
        profile = SourcedProfile.new(
          account: account,
          uid: SecureRandom.uuid,
          provider: "test",
          emails: [],
          email: nil
        )

        profile.send(:extract_contacts_from_arrays)

        expect(profile.email).to be_nil
      end
    end

    context "quando emails é nil" do
      it "não gera erro" do
        profile = SourcedProfile.new(
          account: account,
          uid: SecureRandom.uuid,
          provider: "test",
          emails: nil,
          email: nil
        )

        expect { profile.send(:extract_contacts_from_arrays) }.not_to raise_error
      end
    end

    context "quando phones é array de strings" do
      it "extrai o primeiro telefone corretamente" do
        profile = SourcedProfile.new(
          account: account,
          uid: SecureRandom.uuid,
          provider: "test",
          phones: [ "+55 11 99999-9999", "+55 11 88888-8888" ],
          phone: nil
        )

        profile.send(:extract_contacts_from_arrays)

        expect(profile.phone).to eq("+55 11 99999-9999")
        expect(profile.mobile_phone).to eq("+55 11 88888-8888")
      end
    end

    context "quando phones é array de hashes" do
      it "extrai o primeiro telefone do hash corretamente" do
        profile = SourcedProfile.new(
          account: account,
          uid: SecureRandom.uuid,
          provider: "test",
          phones: [ { "phone" => "+55 11 99999-9999" }, { "phone" => "+55 11 88888-8888" } ],
          phone: nil
        )

        profile.send(:extract_contacts_from_arrays)

        expect(profile.phone).to eq("+55 11 99999-9999")
        expect(profile.mobile_phone).to eq("+55 11 88888-8888")
      end
    end
  end

  describe "criação de perfil com emails array de strings" do
    it "cria perfil com sucesso e popula email principal" do
      profile = SourcedProfile.create!(
        account: account,
        uid: SecureRandom.uuid,
        provider: "pearch",
        external_id: "test-profile-#{SecureRandom.hex(4)}",
        name: "Test User",
        emails: [ "test@company.com", "test@personal.com" ],
        email: nil
      )

      profile.reload

      expect(profile.emails).to eq([ "test@company.com", "test@personal.com" ])
      expect(profile.email).to eq("test@company.com")
      expect(profile.secondary_email).to eq("test@personal.com")
    end

    it "cria perfil com email explícito e array de emails" do
      profile = SourcedProfile.create!(
        account: account,
        uid: SecureRandom.uuid,
        provider: "pearch",
        external_id: "test-profile-#{SecureRandom.hex(4)}",
        name: "Test User",
        email: "primary@company.com",
        emails: [ "other1@company.com", "other2@company.com" ]
      )

      profile.reload

      expect(profile.email).to eq("primary@company.com")
      expect(profile.emails).to eq([ "other1@company.com", "other2@company.com" ])
    end
  end

  describe "criação de perfil com phones array de strings" do
    it "cria perfil com sucesso e popula phone e mobile_phone" do
      profile = SourcedProfile.create!(
        account: account,
        uid: SecureRandom.uuid,
        provider: "pearch",
        external_id: "test-profile-#{SecureRandom.hex(4)}",
        name: "Test User",
        phones: [ "+55 11 99999-9999", "+55 11 88888-8888" ],
        phone: nil
      )

      profile.reload

      expect(profile.phones).to eq([ "+55 11 99999-9999", "+55 11 88888-8888" ])
      expect(profile.phone).to eq("+55 11 99999-9999")
      expect(profile.mobile_phone).to eq("+55 11 88888-8888")
    end

    it "cria perfil com phone explícito e array de phones" do
      profile = SourcedProfile.create!(
        account: account,
        uid: SecureRandom.uuid,
        provider: "pearch",
        external_id: "test-profile-#{SecureRandom.hex(4)}",
        name: "Test User",
        phone: "+55 11 99999-9999",
        phones: [ "+55 11 88888-8888", "+55 11 77777-7777" ]
      )

      profile.reload

      expect(profile.phone).to eq("+55 11 99999-9999")
      expect(profile.phones).to eq([ "+55 11 88888-8888", "+55 11 77777-7777" ])
    end

    it "cria perfil com apenas um telefone no array" do
      profile = SourcedProfile.create!(
        account: account,
        uid: SecureRandom.uuid,
        provider: "pearch",
        external_id: "test-profile-#{SecureRandom.hex(4)}",
        name: "Test User",
        phones: [ "+55 11 99999-9999" ],
        phone: nil
      )

      profile.reload

      expect(profile.phones).to eq([ "+55 11 99999-9999" ])
      expect(profile.phone).to eq("+55 11 99999-9999")
      expect(profile.mobile_phone).to be_nil
    end
  end
end
