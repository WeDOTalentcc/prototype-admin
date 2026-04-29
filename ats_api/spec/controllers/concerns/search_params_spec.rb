# frozen_string_literal: true

require 'rails_helper'

RSpec.describe SearchParams do
  let(:test_class) do
    Class.new do
      include SearchParams
      attr_accessor :params, :current_user

      def initialize(params, current_user)
        @params = ActionController::Parameters.new(params)
        @current_user = current_user
      end
    end
  end

  let(:current_user) { create(:user) }
  let(:instance) { test_class.new(test_params, current_user) }

  describe '#parse_json_param' do
    context 'with blank value' do
      let(:test_params) { {} }

      it 'returns default hash' do
        result = instance.parse_json_param(nil)
        expect(result).to eq({})
      end

      it 'returns custom default' do
        result = instance.parse_json_param('', [])
        expect(result).to eq([])
      end
    end

    context 'with ActionController::Parameters' do
      let(:test_params) { {} }

      it 'converts to unsafe hash' do
        params = ActionController::Parameters.new({ key: 'value' })
        result = instance.parse_json_param(params)
        expect(result).to eq({ 'key' => 'value' })
      end
    end

    context 'with JSON string' do
      let(:test_params) { {} }

      it 'parses valid JSON' do
        result = instance.parse_json_param('{"key": "value"}')
        expect(result).to eq({ 'key' => 'value' })
      end

      it 'returns default on parse error' do
        result = instance.parse_json_param('invalid json')
        expect(result).to eq({})
      end
    end

    context 'with non-string value' do
      let(:test_params) { {} }

      it 'returns value as is' do
        result = instance.parse_json_param({ key: 'value' })
        expect(result).to eq({ key: 'value' })
      end
    end
  end

  describe '#search_with_pin' do
    let(:test_params) do
      {
        search: 'test',
        order: { name: 'asc' }
      }
    end

    it 'includes boost_where with current user pin' do
      result = instance.search_with_pin
      expect(result[:boost_where]).to eq({ 'pin_user_ids' => current_user.id })
    end

    it 'merges score desc with order params' do
      result = instance.search_with_pin
      expect(result[:order][:_score]).to eq('desc')
      expect(result[:order]['name']).to eq('asc')
    end

    it 'includes where and custom params' do
      result = instance.search_with_pin
      expect(result).to have_key(:where)
    end
  end

  describe '#search_with_pin_and_confidential' do
    let(:test_params) do
      {
        search: 'test',
        order: { name: 'asc' }
      }
    end

    it 'includes boost_where with current user pin' do
      result = instance.search_with_pin_and_confidential
      expect(result[:boost_where]).to eq({ 'pin_user_ids' => current_user.id })
    end

    it 'adds confidential OR conditions' do
      result = instance.search_with_pin_and_confidential
      expect(result[:where][:_or]).to include(
        { confidential_user_ids: current_user.id },
        { confidential_user_ids: [ nil ] },
        { confidential_user_ids: nil }
      )
    end

    it 'merges score desc with order params' do
      result = instance.search_with_pin_and_confidential
      expect(result[:order][:_score]).to eq('desc')
      expect(result[:order]['name']).to eq('asc')
    end
  end

  describe '#search_params' do
    context 'without search param' do
      let(:test_params) { {} }

      it 'defaults to wildcard' do
        result = instance.search_params
        expect(result).to eq('*')
      end
    end

    context 'with search param' do
      let(:test_params) { { search: 'TeSt SeArCh' } }

      it 'converts to lowercase' do
        result = instance.search_params
        expect(result).to eq('test search')
      end
    end
  end

  describe '#custom_params' do
    let(:test_params) do
      {
        extra_params: { custom: 'value' },
        entity_column_id: 123
      }
    end

    it 'includes where params' do
      result = instance.custom_params
      expect(result).to have_key(:where)
    end

    it 'includes order params' do
      result = instance.custom_params
      expect(result).to have_key(:order)
    end

    it 'includes extra_params' do
      result = instance.custom_params
      expect(result[:extra_params]).to be_a(ActionController::Parameters)
      expect(result[:extra_params]['custom']).to eq('value')
    end

    it 'includes entity_column_id' do
      result = instance.custom_params
      expect(result[:entity_column_id]).to eq(123)
    end
  end

  describe '#order_params' do
    context 'with wildcard search and no order' do
      let(:test_params) { { search: '*' } }

      it 'defaults to created_at desc' do
        result = instance.order_params
        expect(result).to eq({ created_at: 'desc' })
      end
    end

    context 'with order param' do
      let(:test_params) { { order: { name: 'asc' } } }

      it 'returns parsed order' do
        result = instance.order_params
        expect(result['name']).to eq('asc')
      end
    end

    context 'with score in order' do
      let(:test_params) { { order: { score: 'desc' } } }

      it 'converts score to _score' do
        result = instance.order_params
        expect(result['_score']).to eq('desc')
      end
    end
  end

  describe '#limit_params' do
    context 'without limit param' do
      let(:test_params) { {} }

      it 'defaults to 30' do
        result = instance.limit_params
        expect(result).to eq(30)
      end
    end

    context 'with limit param' do
      let(:test_params) { { limit: 50 } }

      it 'returns specified limit' do
        result = instance.limit_params
        expect(result).to eq(50)
      end
    end
  end

  describe '#where_params' do
    context 'with is_favorited filter' do
      let(:test_params) do
        {
          filter: {
            is_favorited: [ 'Favoritado' ]
          }
        }
      end

      it 'converts is_favorited to favorite_user_ids with current user id' do
        result = instance.where_params
        expect(result[:favorite_user_ids]).to eq(current_user.id)
      end

      it 'does not create LIKE condition for is_favorited' do
        result = instance.where_params
        expect(result).not_to have_key(:is_favorited)
      end
    end

    context 'with multiple filters including is_favorited' do
      let(:test_params) do
        {
          filter: {
            is_favorited: [ 'Favoritado' ],
            name: 'John'
          }
        }
      end

      it 'processes both filters correctly' do
        result = instance.where_params
        expect(result[:favorite_user_ids]).to eq(current_user.id)
        expect(result[:name]).to eq({ like: '%john%' })
      end
    end

    context 'with where params' do
      let(:test_params) do
        {
          where: {
            is_deleted: false,
            remote_work: 'true'
          }
        }
      end

      it 'converts boolean strings to actual booleans' do
        result = instance.where_params
        expect(result[:is_deleted]).to eq(false)
        expect(result[:remote_work]).to eq(true)
      end
    end

    context 'with numeric hash keys in filter' do
      let(:test_params) do
        {
          filter: {
            city: { '0' => 'São Paulo', '1' => 'Rio de Janeiro' }
          }
        }
      end

      it 'converts numeric hash to array and creates OR conditions' do
        result = instance.where_params
        expect(result[:_or]).to be_an(Array)
        expect(result[:_or].length).to eq(2)
        expect(result[:_or]).to include(
          { city: { like: '%são paulo%' } },
          { city: { like: '%rio de janeiro%' } }
        )
      end
    end

    context 'with id filter' do
      let(:test_params) do
        {
          filter: {
            id: '123'
          }
        }
      end

      it 'converts string id to integer without LIKE' do
        result = instance.where_params
        expect(result[:id]).to eq(123)
        expect(result[:id]).to be_an(Integer)
      end
    end

    context 'with external_id filter' do
      let(:test_params) do
        {
          filter: {
            external_id: 'abc123'
          }
        }
      end

      it 'keeps non-numeric external_id as string' do
        result = instance.where_params
        expect(result[:external_id]).to eq('abc123')
        expect(result[:external_id]).to be_a(String)
      end
    end

    context 'with array of strings filter' do
      let(:test_params) do
        {
          filter: {
            role_name: [ 'Developer', 'Manager' ]
          }
        }
      end

      it 'creates OR conditions with LIKE for each value' do
        result = instance.where_params
        expect(result[:_or]).to be_an(Array)
        expect(result[:_or].length).to eq(2)
        expect(result[:_or]).to include(
          { role_name: { like: '%developer%' } },
          { role_name: { like: '%manager%' } }
        )
      end
    end

    context 'with string filter' do
      let(:test_params) do
        {
          filter: {
            name: 'John Doe'
          }
        }
      end

      it 'creates LIKE condition with lowercase' do
        result = instance.where_params
        expect(result[:name]).to eq({ like: '%john doe%' })
      end
    end

    context 'with integer filter' do
      let(:test_params) do
        {
          filter: {
            age: 30
          }
        }
      end

      it 'keeps integer as is' do
        result = instance.where_params
        expect(result[:age]).to eq(30)
        expect(result[:age]).to be_an(Integer)
      end
    end

    context 'with hash filter' do
      let(:test_params) do
        {
          filter: {
            salary: { gte: 5000 }
          }
        }
      end

      it 'keeps hash structure' do
        result = instance.where_params
        expect(result[:salary]).to eq({ gte: 5000 })
      end
    end

    context 'with empty params' do
      let(:test_params) { {} }

      it 'returns empty symbolized hash' do
        result = instance.where_params
        expect(result).to eq({})
      end
    end

    context 'with base params' do
      let(:test_params) do
        {
          filter: {
            name: 'John'
          }
        }
      end

      it 'merges with base params' do
        result = instance.where_params({ account_id: 1 })
        expect(result[:account_id]).to eq(1)
        expect(result[:name]).to eq({ like: '%john%' })
      end
    end
  end
end
