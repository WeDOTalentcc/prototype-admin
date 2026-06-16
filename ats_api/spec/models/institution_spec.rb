
require 'rails_helper'

RSpec.describe Institution, type: :model do
  describe 'attributes' do
    it 'defaults approved to false' do
      institution = Institution.new
      expect(institution.approved).to be(false)
    end

    it 'defaults account_id to an empty array' do
      institution = Institution.new
      expect(institution.account_id).to eq([])
    end
  end
end
