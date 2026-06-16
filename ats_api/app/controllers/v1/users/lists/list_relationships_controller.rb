module V1
  module Users
    module Lists
      class ListRelationshipsController < V1::Users::ApplicationController
        before_action :set_list
        before_action :set_list_relationship, only: %i[show update destroy]
        before_action :global_search_params, only: %i[index index_by_reference]

        def index
          authorize ListRelationship
          @reference_type = params[:reference_type]

          unless @reference_type.present?
            return render_simple_error("reference_type is required", status: :bad_request)
          end

          search_params_valid = @search_params || global_search_params
          search_params_valid = search_params_valid.dup
          search_params_valid[:where] ||= {}
          search_params_valid[:where].merge!({ list_ids: [ @list.id ] })

          where_param = URI.encode_www_form_component(search_params_valid[:where].to_json)
          filter_param = URI.encode_www_form_component(params[:filter] || "")
          order_param = URI.encode_www_form_component(params[:order] || "")
          search_param = URI.encode_www_form_component(params[:search] || "")

          extra_params = URI.encode_www_form_component(
            "list_relationships(list_id,general_comments,list_relationship_id,condition|list_id=#{@list.id}|)"
          )

          redirect_to "/v1/users/#{@reference_type.downcase.pluralize}?" +
                     "page=#{params[:page]}&where=#{where_param}&search=#{search_param}" +
                     "&order=#{order_param}&filter=#{filter_param}" +
                     "&extra_params=#{extra_params}&list_id=#{@list.id}"
        end

        def index_by_reference
          @reference_type = params[:reference_type]

          unless @reference_type.present?
            return render_simple_error("reference_type is required", status: :bad_request)
          end

          search_params_valid = @search_params || global_search_params
          search_params_valid = search_params_valid.dup

          search_params_valid[:where] ||= {}

          if search_params_valid[:where][:id].present?
            search_params_valid[:where][:reference_id] = search_params_valid[:where][:id]
            search_params_valid[:where].delete(:id)
          end

          search_params_valid[:where].merge!({
            list_id: [ @list.id ],
            reference_type: @reference_type.singularize.classify,
            is_deleted: [ false, nil ],
            account_id: @current_user.account_id
          })

          perform_search(
            model: ListRelationship,
            serializer: ListRelationshipSerializer,
            search_with_pin: search_params_valid
          )
        end

        def show
          authorize @list_relationship
          render_success(@list_relationship, serializer: ListRelationshipSerializer)
        end

        def create
          authorize ListRelationship
          @list_relationship = ListRelationship.new(make_params)

          if @list_relationship.save
            update_list_count(@list_relationship.reference_type)
            return render_success(@list_relationship, serializer: ListRelationshipSerializer, status: :created)
          end

          render_error(@list_relationship, status: :unprocessable_entity)
        end

        def update
          authorize @list_relationship
          @previous_reference_type = @list_relationship.reference_type

          if @list_relationship.update(make_params.except(:list_id, :account_id))
            update_list_count(@list_relationship.reference_type, @previous_reference_type)
            return render_success(@list_relationship, serializer: ListRelationshipSerializer)
          end

          render_error(@list_relationship)
        end

        def destroy
          authorize @list_relationship
          @reference_type = @list_relationship.reference_type
          @list_relationship.update(is_deleted: true)
          update_list_count(@reference_type)

          render_success({ message: "List relationship removed successfully" })
        end

        def sort
          authorize ListRelationship, :sort?
          params[:list_relationships].each do |relationship|
            ListRelationship
              .find_by(id: relationship[:id], account_id: @current_user.account_id)
              &.update(position: relationship[:position])
          end

          render_success({ message: "List relationships sorted successfully" })
        end

        def collection
          authorize ListRelationship, :collection?
          if params[:list_collection] && params[:list_collection][:select_all_params].present?
            select_all_params = get_select_all_params
            ListRelationshipJob.perform_later(
              select_all_params.to_h,
              @list.id,
              @current_user.id,
              @current_user.account_id
            )
            return render_success({ status: "processing" })
          end

          return render_simple_error("collections parameter is required", status: :bad_request) unless list_collection_params

          collections_data = list_collection_params[:collections]&.map do |ref|
            {
              reference_type: ref[:reference_type],
              reference_id: ref[:reference_id],
              general_comments: ref[:general_comments]
            }
          end

          if collections_data.present?
            ListRelationshipJob.perform_later(
              nil,
              @list.id,
              @current_user.id,
              @current_user.account_id,
              "create",
              collections_data
            )
            return render_success({ status: "processing" })
          end

          render_simple_error("collections parameter is required", status: :bad_request)
        end

        def delete_collection
          authorize ListRelationship, :delete_collection?
          if params[:list_collection] && params[:list_collection][:select_all_params].present?
            select_all_params = get_select_all_params
            ListRelationshipJob.perform_later(
              select_all_params.to_h,
              @list.id,
              @current_user.id,
              @current_user.account_id,
              "delete"
            )
            return render_success({ status: "processing" })
          end

          return render_simple_error("collections parameter is required", status: :bad_request) unless list_collection_params

          collections_data = list_collection_params[:collections]&.map do |ref|
            {
              reference_type: ref[:reference_type],
              reference_id: ref[:reference_id],
              general_comments: ref[:general_comments]
            }
          end

          if collections_data.present?
            ListRelationshipJob.perform_later(
              nil,
              @list.id,
              @current_user.id,
              @current_user.account_id,
              "delete",
              collections_data
            )
            return render_success({ status: "processing" })
          end

          render_simple_error("collections parameter is required", status: :bad_request)
        end

        private

        def list_collection_params
          params.require(:list_collection).permit(
            collections: %i[reference_type reference_id general_comments]
          )
        end

        def get_select_all_params
          params[:list_collection][:select_all_params].permit!
        end

        def set_list_relationship
          @list_relationship = ListRelationship.find_by(
            id: params[:relationship_id],
            list_id: @list.id,
            account_id: @current_user.account_id
          )

          render_not_found("List relationship") unless @list_relationship
        end

        def set_list
          id = params[:id] || params[:list_id]
          @list = List.find_by(id: id, account_id: @current_user.account_id)
          render_not_found("List") unless @list
        end

        def make_params
          attribute_params = list_relationship_params
          attribute_params[:list_id] = @list.id
          attribute_params[:account_id] = @current_user.account_id

          last_position = ListRelationship
                           .where(list_id: @list.id)
                           .maximum(:position) || 0

          attribute_params[:position] = last_position + 1
          attribute_params
        end

        def list_relationship_params
          params.require(:list_relationship).permit(
            :reference_type,
            :reference_id,
            :position,
            :general_comments,
            :score
          )
        end

        def update_list_count(reference_type, previous_reference_type = nil)
          @list.count_relationships
        end

        def global_search_params
          @search_params = {
            where: where_params,
            order: order_params,
            page: params[:page] || 1,
            limit: limit_params
          }
        end
      end
    end
  end
end
