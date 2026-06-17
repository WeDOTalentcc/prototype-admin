# frozen_string_literal: true

class ImportCsvChannel < ApplicationCable::Channel
  private

  def after_authentication
    data_file = DataFile.find_by(id: params[:data_file_id])
    return unless data_file && data_file.account_id == current_user.account_id

    stream_for data_file
  end
end
