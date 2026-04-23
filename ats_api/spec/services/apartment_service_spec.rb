# frozen_string_literal: true

require 'rails_helper'

RSpec.describe ApartmentService do
  describe '.create' do
    let(:tenant_name) { 'test_tenant' }

    context 'when tenant name is provided' do
      it 'creates new tenant' do
        expect(Apartment::Tenant).to receive(:create).with(tenant_name)

        described_class.create(tenant_name)
      end
    end

    context 'when tenant name is nil' do
      it 'does not create tenant' do
        expect(Apartment::Tenant).not_to receive(:create)

        described_class.create(nil)
      end
    end

    context 'when tenant name is blank string' do
      it 'creates tenant even with blank string' do
        expect(Apartment::Tenant).to receive(:create).with('')

        described_class.create('')
      end
    end

    context 'when Apartment::Tenant raises error' do
      before do
        allow(Apartment::Tenant).to receive(:create).and_raise(Apartment::TenantNotFound)
      end

      it 'propagates exception' do
        expect { described_class.create(tenant_name) }.to raise_error(Apartment::TenantNotFound)
      end
    end
  end
end
