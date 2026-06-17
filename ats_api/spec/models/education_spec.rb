# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Education, type: :model do
  describe 'associations' do
    it { should belong_to(:candidate) }
    it { should belong_to(:account) }
    it { should belong_to(:institution).optional }
    it { should belong_to(:study_area).optional }
    it { should belong_to(:city).optional }
  end

  describe 'find_or_create_associations_by_name' do
    let(:account) { create(:account) }
    let(:candidate) { create(:candidate) }

    context 'when institution_name is provided' do
      it 'creates a new institution if it does not exist' do
        education = build(:education, institution: nil, institution_name: 'Universidade Inexistente', account: account)
        expect { education.save }.to change(Institution, :count).by(1)
        expect(education.institution.name).to eq('Universidade Inexistente')
        expect(education.institution.account).to eq(account)
      end

      it 'finds an existing institution and associates it' do
        existing_institution = create(:institution, name: 'Universidade Existente', account: account)
        education = build(:education, institution: nil, institution_name: 'Universidade Existente', account: account)
        expect { education.save }.not_to change(Institution, :count)
        expect(education.institution).to eq(existing_institution)
      end
    end

    context 'when study_area_name is provided' do
      it 'creates a new study area if it does not exist' do
        education = build(:education, study_area: nil, study_area_name: 'Área Inexistente', account: account)
        expect { education.save }.to change(StudyArea, :count).by(1)
        expect(education.study_area.name).to eq('Área Inexistente')
      end

      it 'finds an existing study area and associates it' do
        existing_study_area = create(:study_area, name: 'Área Existente', account: account)
        education = build(:education, study_area: nil, study_area_name: 'Área Existente', account: account)
        expect { education.save }.not_to change(StudyArea, :count)
        expect(education.study_area).to eq(existing_study_area)
      end
    end
  end
end
