require 'rails_helper'

RSpec.describe RemunerationRelationships::BulkUpsertService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:remuneration) { create(:remuneration, account: account, user: user) }
  let(:job1) { create(:job, account: account) }
  let(:job2) { create(:job, account: account) }

  describe '#call' do
    context 'when creating new relationships' do
      let(:relationships_params) do
        [
          {
            remuneration_id: remuneration.id,
            reference_type: "Job",
            reference_id: job1.id,
            currency: "BRL",
            value: 5000.00,
            contract_type: [ "CLT" ]
          },
          {
            remuneration_id: remuneration.id,
            reference_type: "Job",
            reference_id: job2.id,
            currency: "USD",
            value: 3000.00,
            contract_type: [ "PJ" ]
          }
        ]
      end

      subject(:service) { described_class.new(relationships_params: relationships_params, current_user: user) }

      it 'creates all relationships' do
        expect { service.call }.to change(RemunerationRelationship, :count).by(2)
      end

      it 'returns success result with created items' do
        result = service.call

        expect(result[:created].size).to eq(2)
        expect(result[:updated].size).to eq(0)
        expect(result[:total]).to eq(2)
        expect(result[:errors]).to be_empty
      end

      it 'assigns correct attributes' do
        result = service.call

        first_relationship = result[:created].first
        expect(first_relationship.remuneration_id).to eq(remuneration.id)
        expect(first_relationship.reference_type).to eq("Job")
        expect(first_relationship.reference_id).to eq(job1.id)
        expect(first_relationship.account_id).to eq(user.account_id)
        expect(first_relationship.user_id).to eq(user.id)
        expect(first_relationship.is_deleted).to eq(false)
      end
    end

    context 'when updating existing relationships' do
      let!(:existing_relationship) do
        create(:remuneration_relationship,
          account: account,
          user: user,
          remuneration: remuneration,
          reference_type: "Job",
          reference_id: job1.id,
          value: 4000.00,
          currency: "BRL"
        )
      end

      let(:relationships_params) do
        [
          {
            remuneration_id: remuneration.id,
            reference_type: "Job",
            reference_id: job1.id,
            currency: "USD",
            value: 6000.00
          }
        ]
      end

      subject(:service) { described_class.new(relationships_params: relationships_params, current_user: user) }

      it 'does not create new relationship' do
        expect { service.call }.not_to change(RemunerationRelationship, :count)
      end

      it 'updates existing relationship' do
        result = service.call

        expect(result[:created].size).to eq(0)
        expect(result[:updated].size).to eq(1)
        expect(result[:total]).to eq(1)
        expect(result[:errors]).to be_empty

        existing_relationship.reload
        expect(existing_relationship.value).to eq(6000.00)
        expect(existing_relationship.currency).to eq("USD")
      end
    end

    context 'when updating by id' do
      let!(:existing_relationship) do
        create(:remuneration_relationship,
          account: account,
          user: user,
          remuneration: remuneration,
          reference_type: "Job",
          reference_id: job1.id,
          value: 4000.00,
          currency: "BRL"
        )
      end

      let(:relationships_params) do
        [
          {
            id: existing_relationship.id,
            currency: "USD",
            value: 7000.00
          }
        ]
      end

      subject(:service) { described_class.new(relationships_params: relationships_params, current_user: user) }

      it 'does not create new relationship' do
        expect { service.call }.not_to change(RemunerationRelationship, :count)
      end

      it 'updates existing relationship by id' do
        result = service.call

        expect(result[:created].size).to eq(0)
        expect(result[:updated].size).to eq(1)
        expect(result[:total]).to eq(1)

        existing_relationship.reload
        expect(existing_relationship.value).to eq(7000.00)
        expect(existing_relationship.currency).to eq("USD")
      end
    end

    context 'when mixing creates and updates' do
      let!(:existing_relationship) do
        create(:remuneration_relationship,
          account: account,
          user: user,
          remuneration: remuneration,
          reference_type: "Job",
          reference_id: job1.id,
          value: 4000.00
        )
      end

      let(:relationships_params) do
        [
          {
            remuneration_id: remuneration.id,
            reference_type: "Job",
            reference_id: job1.id,
            value: 5000.00
          },
          {
            remuneration_id: remuneration.id,
            reference_type: "Job",
            reference_id: job2.id,
            value: 3000.00
          }
        ]
      end

      subject(:service) { described_class.new(relationships_params: relationships_params, current_user: user) }

      it 'creates new and updates existing' do
        expect { service.call }.to change(RemunerationRelationship, :count).by(1)
      end

      it 'returns correct counts' do
        result = service.call

        expect(result[:created].size).to eq(1)
        expect(result[:updated].size).to eq(1)
        expect(result[:total]).to eq(2)
      end
    end

    context 'with invalid params' do
      let(:relationships_params) do
        [
          {
            currency: "BRL",
            value: 5000.00
          }
        ]
      end

      subject(:service) { described_class.new(relationships_params: relationships_params, current_user: user) }

      it 'does not create any relationship' do
        expect { service.call }.not_to change(RemunerationRelationship, :count)
      end

      it 'returns error result' do
        result = service.call

        expect(result[:errors]).not_to be_empty
        expect(result[:errors].first[:errors]).to include("Campos obrigatórios")
        expect(result[:created]).to be_empty
        expect(result[:updated]).to be_empty
      end
    end

    context 'when one item is invalid' do
      let(:relationships_params) do
        [
          {
            remuneration_id: remuneration.id,
            reference_type: "Job",
            reference_id: job1.id,
            value: 5000.00
          },
          {
            reference_type: "Job",
            reference_id: job2.id
          }
        ]
      end

      subject(:service) { described_class.new(relationships_params: relationships_params, current_user: user) }

      it 'rolls back transaction and creates nothing' do
        expect { service.call }.not_to change(RemunerationRelationship, :count)
      end

      it 'returns errors' do
        result = service.call

        expect(result[:errors]).not_to be_empty
        expect(result[:errors].first[:errors]).to include("Campos obrigatórios")
      end
    end

    context 'when relationship is soft deleted' do
      let!(:deleted_relationship) do
        create(:remuneration_relationship,
          account: account,
          user: user,
          remuneration: remuneration,
          reference_type: "Job",
          reference_id: job1.id,
          value: 4000.00,
          is_deleted: true
        )
      end

      let(:relationships_params) do
        [
          {
            remuneration_id: remuneration.id,
            reference_type: "Job",
            reference_id: job1.id,
            value: 5000.00
          }
        ]
      end

      subject(:service) { described_class.new(relationships_params: relationships_params, current_user: user) }

      it 'creates new relationship instead of updating deleted one' do
        expect { service.call }.to change(RemunerationRelationship.where(is_deleted: false), :count).by(1)
      end

      it 'returns correct counts' do
        result = service.call

        expect(result[:created].size).to eq(1)
        expect(result[:updated].size).to eq(0)
      end
    end
  end
end
