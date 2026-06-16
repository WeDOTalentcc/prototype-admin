require 'rails_helper'

RSpec.describe Experience, type: :model do
  describe 'associations' do
    it { should belong_to(:account) }
    it { should belong_to(:user).optional }
    it { should belong_to(:occupation) }
    it { should belong_to(:company) }
  end

  describe 'validations' do
    subject { build(:experience) }

    it { should validate_presence_of(:occupation_id) }
    it { should validate_presence_of(:company_id) }
    it { should validate_presence_of(:start_date) }
  end

  describe 'find_or_create_company functionality' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:occupation) { create(:occupation, account: account) }

    context 'when company_name is provided' do
      it 'finds existing company by name (case insensitive)' do
        existing_company = create(:company, name: 'google', account: account)

        experience = build(:experience,
          account: account,
          user: user,
          occupation: occupation,
          company_name: 'Google'
        )

        expect { experience.valid? }.not_to change(Company, :count)
        expect(experience.company_id).to eq(existing_company.id)
      end

      it 'creates new company when not found' do
        experience = build(:experience,
          account: account,
          user: user,
          occupation: occupation,
          company_name: 'New Company'
        )

        expect { experience.valid? }.to change(Company, :count).by(1)
        expect(experience.company.name).to eq('new company')
        expect(experience.company.account).to eq(account)
        expect(experience.company.user).to eq(user)
      end

      it 'ignores deleted companies' do
        create(:company, name: 'google', account: account, is_deleted: true)

        experience = build(:experience,
          account: account,
          user: user,
          occupation: occupation,
          company_name: 'Google'
        )

        expect { experience.valid? }.to change(Company, :count).by(1)
        expect(experience.company.name).to eq('google')
        expect(experience.company.is_deleted).to eq(false)
      end

      it 'scopes to current account' do
        other_account = create(:account)
        create(:company, name: 'google', account: other_account)

        experience = build(:experience,
          account: account,
          user: user,
          occupation: occupation,
          company_name: 'Google'
        )

        expect { experience.valid? }.to change(Company, :count).by(1)
        expect(experience.company.account).to eq(account)
      end
    end
  end

  describe 'find_or_create_occupation functionality' do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:company) { create(:company, account: account) }

    context 'when occupation_name is provided' do
      it 'finds existing occupation by name (case insensitive)' do
        existing_occupation = create(:occupation, name: 'developer', account: account)

        experience = build(:experience,
          account: account,
          user: user,
          company: company,
          occupation_name: 'Developer'
        )

        expect { experience.valid? }.not_to change(Occupation, :count)
        expect(experience.occupation_id).to eq(existing_occupation.id)
      end

      it 'creates new occupation when not found' do
        experience = build(:experience,
          account: account,
          user: user,
          company: company,
          occupation_name: 'Designer'
        )

        expect { experience.valid? }.to change(Occupation, :count).by(1)
        expect(experience.occupation.name).to eq('Designer')
        expect(experience.occupation.account).to eq(account)
        expect(experience.occupation.user).to eq(user)
      end

      it 'ignores deleted occupations' do
        create(:occupation, name: 'developer', account: account, is_deleted: true)

        experience = build(:experience,
          account: account,
          user: user,
          company: company,
          occupation_name: 'Developer'
        )

        expect { experience.valid? }.to change(Occupation, :count).by(1)
        expect(experience.occupation.name).to eq('Developer')
        expect(experience.occupation.is_deleted).to eq(false)
      end

      it 'scopes to current account' do
        other_account = create(:account)
        create(:occupation, name: 'developer', account: other_account)

        experience = build(:experience,
          account: account,
          user: user,
          company: company,
          occupation_name: 'Developer'
        )

        expect { experience.valid? }.to change(Occupation, :count).by(1)
        expect(experience.occupation.account).to eq(account)
      end
    end
  end

  describe '#search_data' do
    let(:experience) { create(:experience) }

    it 'returns the correct search data structure' do
      search_data = experience.search_data

      expect(search_data).to include(
        :id,
        :description,
        :reasons_leaving,
        :contract_type,
        :occupation_name,
        :company_name,
        :start_date,
        :end_date,
        :work_here
      )

      expect(search_data[:occupation_name]).to eq(experience.occupation.name)
      expect(search_data[:company_name]).to eq(experience.company.name)
    end
  end
end
